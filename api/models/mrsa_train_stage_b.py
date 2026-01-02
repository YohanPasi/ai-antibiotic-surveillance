import pandas as pd
import numpy as np
import xgboost as xgb
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OrdinalEncoder
from sklearn.metrics import accuracy_score, roc_auc_score, confusion_matrix, classification_report
from sqlalchemy import create_engine
import shap
import joblib
import json
import os
import sys

# DATABASE CONNECTION
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ast_user:ast_password_2024@db:5432/ast_db")
engine = create_engine(DATABASE_URL)

ARTIFACT_DIR = "/app/models/mrsa_artifacts"
os.makedirs(ARTIFACT_DIR, exist_ok=True)

def run_mrsa_stage_b():
    print("🧪 Starting MRSA Stage B: Training & Feature Engineering...")

    # 1. LOAD DATA
    print("   - Loading data from DB...")
    df = pd.read_sql("SELECT * FROM mrsa_raw_clean", engine)
    print(f"     Loaded {len(df)} rows.")

    # 2. PREPROCESSING
    # Drop metadata
    drop_cols = ['id', 'entry_date', 'bht']
    df = df.drop(columns=[c for c in drop_cols if c in df.columns])

    # Target
    y = df['mrsa_label']
    X = df.drop(columns=['mrsa_label'])

    # A. Missing Values
    print("   - Handling missing values...")
    X['age'] = X['age'].fillna(X['age'].median())
    # Handle growth_time - convert to numeric if it's string (e.g. "24h") or mixed
    X['growth_time'] = pd.to_numeric(X['growth_time'], errors='coerce')
    X['growth_time'] = X['growth_time'].fillna(X['growth_time'].median())
    
    # Fill categorical NAs
    cat_cols = ['ward', 'gender', 'sample_type', 'pus_type', 'cell_count', 'gram_positivity']
    for c in cat_cols:
        if c in X.columns:
            X[c] = X[c].fillna('Unknown')

    # B. Encoding
    print("   - Encoding features...")
    
    # Cell Count: Ordinal Mapping
    # Standardize text first
    X['cell_count'] = X['cell_count'].astype(str).str.lower().str.strip()
    cell_map = {
        'none': 0, 'no wc': 0, 'not seen': 0, '0': 0,
        'rare': 1, '+': 1, 'scanty': 1,
        'few': 2, '++': 2,
        'moderate': 3, '+++': 3,
        'many': 4, 'plenty': 4, '++++': 4,
        'unknown': 0 # Default to 0 risk if unknown
    }
    # Apply map, default to 0 if not found
    X['cell_count_encoded'] = X['cell_count'].map(cell_map).fillna(0)
    X = X.drop(columns=['cell_count'])

    # One-Hot Encoding for others
    # We use pandas get_dummies for simplicity. In prod pipeline, we'd save a OneHotEncoder artifact.
    # For this stage, we'll save the column names to ensure consistency.
    X_encoded = pd.get_dummies(X, columns=['ward', 'gender', 'sample_type', 'pus_type', 'gram_positivity'], drop_first=True) # drop_first=True to reduce collinearity binary classification
    
    # C. Scaling
    print("   - Scaling numeric features...")
    scaler = StandardScaler()
    num_cols = ['age', 'growth_time', 'cell_count_encoded']
    X_encoded[num_cols] = scaler.fit_transform(X_encoded[num_cols])

    # 3. TRAIN/TEST SPLIT
    print("   - Splitting data (70% Train, 15% Val, 15% Test)...")
    # First split 70/30
    X_train, X_temp, y_train, y_temp = train_test_split(X_encoded, y, test_size=0.3, stratify=y, random_state=42)
    # Then split temp 50/50 (15/15)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, stratify=y_temp, random_state=42)

    # 4. MODEL TRAINING (XGBoost)
    print("   - Training XGBoost Classifier...")
    model = XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="logloss",
        random_state=42
    )
    
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False
    )

    # 5. EVALUATION
    print("   - Evaluating model...")
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    auc = roc_auc_score(y_test, y_prob)
    acc = accuracy_score(y_test, y_pred)
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
    
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    npv = tn / (tn + fn) if (tn + fn) > 0 else 0
    ppv = tp / (tp + fp) if (tp + fp) > 0 else 0

    metrics = {
        "AUC": round(auc, 4),
        "Accuracy": round(acc, 4),
        "Sensitivity": round(sensitivity, 4),
        "Specificity": round(specificity, 4),
        "NPV": round(npv, 4),
        "PPV": round(ppv, 4)
    }
    print(f"     Results: {json.dumps(metrics, indent=2)}")

    # 6. SHAP EXPLANATION
    print("   - Generating SHAP values...")
    explainer = shap.TreeExplainer(model)
    # Use a small sample for SHAP to be fast
    shap_values = explainer.shap_values(X_test.iloc[:100])
    
    # 7. SAVE ARTIFACTS
    print("   - Saving artifacts...")
    # Save Model
    joblib.dump(model, os.path.join(ARTIFACT_DIR, "mrsa_xgb_model.pkl"))
    # Save Scaler
    joblib.dump(scaler, os.path.join(ARTIFACT_DIR, "scaler.pkl"))
    # Save Feature Columns (to ensure correct input order/structure for inference)
    with open(os.path.join(ARTIFACT_DIR, "feature_columns.json"), "w") as f:
        json.dump(list(X_encoded.columns), f)
    # Save Metrics
    with open(os.path.join(ARTIFACT_DIR, "training_report.json"), "w") as f:
        json.dump(metrics, f, indent=4)

    print("✅ Stage B Complete: Model trained and artifacts saved.")

if __name__ == "__main__":
    run_mrsa_stage_b()
