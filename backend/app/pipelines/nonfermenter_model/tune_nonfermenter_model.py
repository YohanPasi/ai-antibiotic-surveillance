import os
import optuna
import joblib
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score
from pathlib import Path

# ============================================================
#  PATHS
# ============================================================

# Get project root (5 levels up from this file: nonfermenter_model -> pipelines -> app -> backend -> project_root)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "nonfermenter" / "nonfermenter_clean.csv"
MODEL_OUT = PROJECT_ROOT / "ml" / "nonfer_trends"
MODEL_OUT.mkdir(parents=True, exist_ok=True)


# ============================================================
#  LOAD DATA
# ============================================================

print(f"Loading dataset: {DATA_PATH}")
df = pd.read_csv(DATA_PATH)

if df.empty:
    raise ValueError("Dataset empty. Cannot train.")

TARGET = "carbapenem_resistant"

y = df[TARGET].astype(int)

categorical_cols = ["organism", "sample_type", "ward"]
datetime_col = "collection_time"
numeric_cols = ["hour_of_day"]

# Convert collection_time
df[datetime_col] = pd.to_datetime(df[datetime_col], errors="coerce")
df["hour_of_day"] = df[datetime_col].dt.hour.fillna(0).astype(int)

# Antibiotics used as encoded S/I/R
abx_cols = [
    "meropenem", "imipenem", "ceftazidime", "cefepime",
    "amikacin", "gentamicin", "ciprofloxacin", "colistin"
]

def encode_sir(x):
    if pd.isna(x): 
        return -1
    x = str(x).upper().strip()
    return {"S": 0, "I": 1, "R": 2}.get(x, -1)

for col in abx_cols:
    df[col] = df[col].apply(encode_sir)

X = df[categorical_cols + numeric_cols + abx_cols]


# ============================================================
# PREPROCESSING PIPELINE
# ============================================================

preprocess = ColumnTransformer(
    transformers=[
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_cols),
        ("num", "passthrough", numeric_cols + abx_cols),
    ]
)


# ============================================================
# OPTUNA OBJECTIVE FUNCTION
# ============================================================

def objective(trial):
    param = {
        "objective": "binary",
        "metric": "auc",
        "verbosity": -1,
        "boosting_type": "gbdt",

        "num_leaves": trial.suggest_int("num_leaves", 10, 200),
        "learning_rate": trial.suggest_float("learning_rate", 1e-3, 0.3),
        "max_depth": trial.suggest_int("max_depth", 3, 20),
        "min_data_in_leaf": trial.suggest_int("min_data_in_leaf", 5, 50),

        "feature_fraction": trial.suggest_float("feature_fraction", 0.5, 1.0),
        "bagging_fraction": trial.suggest_float("bagging_fraction", 0.5, 1.0),
        "bagging_freq": trial.suggest_int("bagging_freq", 1, 10),

        "lambda_l1": trial.suggest_float("lambda_l1", 1e-8, 10.0, log=True),
        "lambda_l2": trial.suggest_float("lambda_l2", 1e-8, 10.0, log=True)
    }

    model = lgb.LGBMClassifier(**param)

    pipeline = Pipeline([
        ("prep", preprocess),
        ("model", model),
    ])

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    auc_scores = []

    for train_idx, val_idx in skf.split(X, y):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

        pipeline.fit(X_train, y_train)
        preds = pipeline.predict_proba(X_val)[:, 1]

        auc_scores.append(roc_auc_score(y_val, preds))

    return sum(auc_scores) / len(auc_scores)


# ============================================================
# RUN OPTUNA OPTIMIZATION
# ============================================================

study = optuna.create_study(direction="maximize")
study.optimize(objective, n_trials=60, show_progress_bar=True)

print("Best parameters:", study.best_params)
print("Best AUC:", study.best_value)


# ============================================================
# FINAL MODEL TRAINING USING BEST PARAMS
# ============================================================

best_params = study.best_params
best_params.update({
    "objective": "binary",
    "metric": "auc",
    "verbosity": -1,
})

final_model = lgb.LGBMClassifier(**best_params)

final_pipeline = Pipeline([
    ("prep", preprocess),
    ("model", final_model),
])

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

final_pipeline.fit(X_train, y_train)

test_preds = final_pipeline.predict_proba(X_test)[:, 1]
auc = roc_auc_score(y_test, test_preds)
acc = accuracy_score(y_test, (test_preds > 0.5).astype(int))

print(f"Final Model AUC: {auc}")
print(f"Final Model Accuracy: {acc}")

# SAVE MODEL
MODEL_PATH = MODEL_OUT / "nonfermenter_best_model.pkl"
joblib.dump(final_pipeline, MODEL_PATH)

print(f"Saved optimized model to: {MODEL_PATH}")
