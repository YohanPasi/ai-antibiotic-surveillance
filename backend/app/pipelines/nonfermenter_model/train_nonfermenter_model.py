import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report, confusion_matrix
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from lightgbm import LGBMClassifier

# ============================================
# 1. LOAD DATA
# ============================================

# Get project root (5 levels up from this file: nonfermenter_model -> pipelines -> app -> backend -> project_root)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "nonfermenter" / "nonfermenter_clean.csv"

df = pd.read_csv(DATA_PATH)
print("Loaded dataset:", df.shape)

# ============================================
# 2. BASIC CLEANING
# ============================================

# Convert collection_time to datetime
df["collection_time"] = pd.to_datetime(df["collection_time"], errors="coerce")

# Extract time features
df["collection_month"] = df["collection_time"].dt.month
df["collection_week"] = df["collection_time"].dt.isocalendar().week.astype(int)
df["collection_hour"] = df["collection_time"].dt.hour

# Encode S/I/R values
sir_map = {"S": 0, "I": 1, "R": 2}

ast_cols = [
    "meropenem", "imipenem", "ceftazidime", "cefepime",
    "amikacin", "gentamicin", "ciprofloxacin", "colistin"
]

for col in ast_cols:
    df[col] = df[col].map(sir_map)

# ============================================
# 3. SELECT FEATURES
# ============================================

categorical_cols = ["ward", "sample_type", "organism", "gram"]
numeric_cols = ast_cols + ["collection_month", "collection_week", "collection_hour"]

X = df[categorical_cols + numeric_cols]
y = df["carbapenem_resistant"]

# ============================================
# 4. TRAIN-TEST SPLIT
# ============================================

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ============================================
# 5. PREPROCESSING PIPELINE
# ============================================

preprocessor = ColumnTransformer(
    transformers=[
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_cols),
        ("num", "passthrough", numeric_cols),
    ]
)

# ============================================
# 6. LIGHTGBM MODEL
# ============================================

model = LGBMClassifier(
    n_estimators=300,
    learning_rate=0.05,
    max_depth=-1,
    random_state=42
)

pipeline = Pipeline([
    ("prep", preprocessor),
    ("model", model)
])

# ============================================
# 7. TRAIN MODEL
# ============================================

pipeline.fit(X_train, y_train)

# ============================================
# 8. EVALUATE MODEL
# ============================================

pred = pipeline.predict(X_test)
proba = pipeline.predict_proba(X_test)[:, 1]

print("\nAccuracy:", accuracy_score(y_test, pred))
print("ROC-AUC:", roc_auc_score(y_test, proba))
print("\nClassification report:\n", classification_report(y_test, pred))
print("\nConfusion matrix:\n", confusion_matrix(y_test, pred))

# ============================================
# 9. SAVE MODEL + PREPROCESSOR
# ============================================

# Save to ml/nonfer_trends directory (or create it if it doesn't exist)
MODEL_DIR = PROJECT_ROOT / "ml" / "nonfer_trends"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
MODEL_PATH = MODEL_DIR / "nonfermenter_model.pkl"

joblib.dump(pipeline, MODEL_PATH)
print(f"\nSaved model → {MODEL_PATH}")
