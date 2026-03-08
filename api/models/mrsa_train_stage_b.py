import pandas as pd
import numpy as np
import xgboost as xgb
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, roc_auc_score, confusion_matrix, classification_report
from sqlalchemy import create_engine
import shap
import joblib
import json
import os
import sys

# ── DATABASE CONNECTION ────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ast_user:ast_password_2024@db:5432/ast_db")
engine = create_engine(DATABASE_URL)

ARTIFACT_DIR = "/app/models/mrsa_artifacts"
os.makedirs(ARTIFACT_DIR, exist_ok=True)

MODEL_VERSION = 'v2'

# ── Feature Set v2 (canonical — matches docs/mrsa_features.md) ────────────────
FEATURE_COLS = [
    'ward',
    'sample_type',
    'gram_stain',
    'cell_count_category',
    'growth_time',
    'recent_antibiotic_use',
    'length_of_stay',
]

CATEGORICAL_FEATURES = [
    'ward',
    'sample_type',
    'gram_stain',
    'cell_count_category',
    'recent_antibiotic_use',
]

NUMERIC_FEATURES = [
    'growth_time',
    'length_of_stay',
]


def run_mrsa_stage_b():
    print("🧪 Starting MRSA Stage B: Training & Feature Engineering — Schema v2...")

    # 1. LOAD DATA
    print("   - Loading data from DB...")
    df = pd.read_sql("SELECT * FROM mrsa_raw_clean", engine)
    print(f"     Loaded {len(df)} rows.")

    # 2. DROP METADATA COLUMNS (never features)
    drop_cols = ['id', 'entry_date', 'bht', 'age', 'gender', 'pus_type',
                 'cell_count', 'gram_positivity']  # v1 columns — dropped if present
    df = df.drop(columns=[c for c in drop_cols if c in df.columns])

    # 3. TARGET + FEATURES
    y = df['mrsa_label']
    X = df[FEATURE_COLS].copy()

    # 4. MISSING VALUE HANDLING
    print("   - Handling missing values...")

    # growth_time: -1 sentinel for NULL (non-blood specimens).
    # Do NOT use median imputation — NULL is clinically informative.
    X['growth_time'] = pd.to_numeric(X['growth_time'], errors='coerce').fillna(-1)

    # length_of_stay: 0 is a valid and common default
    X['length_of_stay'] = pd.to_numeric(X['length_of_stay'], errors='coerce').fillna(0)

    # cell_count_category: should already be LOW/MEDIUM/HIGH from ingestion
    # Fallback in case legacy rows have old ordinal values
    cell_ordinal_to_cat = {0: 'LOW', 1: 'LOW', 2: 'MEDIUM', 3: 'HIGH', 4: 'HIGH'}
    if X['cell_count_category'].dtype in [np.int64, np.float64]:
        X['cell_count_category'] = X['cell_count_category'].map(cell_ordinal_to_cat).fillna('LOW')

    for col in CATEGORICAL_FEATURES:
        X[col] = X[col].fillna('Unknown').astype(str)

    # 5. PREPROCESSING PIPELINE
    print("   - Building preprocessing pipeline...")

    # CRITICAL: remainder='drop' — not 'passthrough'.
    # 'passthrough' appends extra columns in undefined order → silent feature mismatch at inference.
    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), CATEGORICAL_FEATURES),
            ('num', StandardScaler(), NUMERIC_FEATURES),
        ],
        remainder='drop'
    )

    # 6. TRAIN / VALIDATION / TEST SPLIT (70 / 15 / 15)
    print("   - Splitting data (70% Train, 15% Val, 15% Test)...")
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.3, stratify=y, random_state=42
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, stratify=y_temp, random_state=42
    )

    # 7. FIT PREPROCESSOR
    X_train_t = preprocessor.fit_transform(X_train)
    X_val_t   = preprocessor.transform(X_val)
    X_test_t  = preprocessor.transform(X_test)

    # 8. MODEL TRAINING (XGBoost — raw features, Pipeline-less for SHAP compatibility)
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
        X_train_t, y_train,
        eval_set=[(X_val_t, y_val)],
        verbose=False
    )

    # 9. EVALUATION
    print("   - Evaluating model...")
    y_pred = model.predict(X_test_t)
    y_prob = model.predict_proba(X_test_t)[:, 1]

    auc = roc_auc_score(y_test, y_prob)
    acc = accuracy_score(y_test, y_pred)
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()

    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    npv = tn / (tn + fn) if (tn + fn) > 0 else 0
    ppv = tp / (tp + fp) if (tp + fp) > 0 else 0

    metrics = {
        "schema_version": MODEL_VERSION,
        "AUC": round(auc, 4),
        "Accuracy": round(acc, 4),
        "Sensitivity": round(sensitivity, 4),
        "Specificity": round(specificity, 4),
        "NPV": round(npv, 4),
        "PPV": round(ppv, 4)
    }
    print(f"     Results: {json.dumps(metrics, indent=2)}")

    # 10. SHAP EXPLANATION (sample)
    print("   - Generating SHAP values (sample)...")
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test_t[:100])

    # 11. SAVE ARTIFACTS
    print("   - Saving artifacts...")

    # Save raw XGBoost model (used by SHAP explain service)
    joblib.dump(model, os.path.join(ARTIFACT_DIR, f"mrsa_xgb_model_{MODEL_VERSION}.pkl"))

    # Save preprocessor (used by SHAP explain service to transform live input)
    joblib.dump(preprocessor, os.path.join(ARTIFACT_DIR, f"mrsa_preprocessor_{MODEL_VERSION}.pkl"))

    # Save feature order lock — inference MUST use this order
    with open(os.path.join(ARTIFACT_DIR, f"feature_columns_{MODEL_VERSION}.json"), "w") as f:
        json.dump(FEATURE_COLS, f, indent=2)

    # Save metrics
    with open(os.path.join(ARTIFACT_DIR, f"stage_b_training_report_{MODEL_VERSION}.json"), "w") as f:
        json.dump(metrics, f, indent=4)

    print("✅ Stage B Complete: Model trained and artifacts saved.")


if __name__ == "__main__":
    run_mrsa_stage_b()
