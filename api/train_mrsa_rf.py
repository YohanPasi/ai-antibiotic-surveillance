import pandas as pd
import numpy as np
import joblib
import json
import os
from datetime import datetime
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score, confusion_matrix, recall_score

# ── Configuration ─────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "postgresql://postgres.zdhvyhijuriggezelyxq:Yohan%26pasi80253327@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres?sslmode=require"

ARTIFACT_DIR = r'/app/models/mrsa_artifacts'
if os.name == 'nt':
    ARTIFACT_DIR = r'd:\Yohan\Project\api\models\mrsa_artifacts'

os.makedirs(ARTIFACT_DIR, exist_ok=True)

# ── Feature Set v2 (canonical — matches docs/mrsa_features.md) ────────────────
MODEL_VERSION = 'v2'

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


def train_rf():
    print("Starting Random Forest Training (Champion) — Schema v2...")

    # 1. Load Data
    engine = create_engine(DATABASE_URL)
    df = pd.read_sql("SELECT * FROM mrsa_raw_clean", engine)
    print(f"Loaded {len(df)} records.")

    # 2. Feature extraction
    X = df[FEATURE_COLS].copy()
    y = df['mrsa_label'].values

    # 3. Preprocessing
    # growth_time: -1 sentinel for NULL (non-blood samples).
    # Do NOT impute with median — NULL is clinically informative (non-blood specimen).
    X['growth_time'] = X['growth_time'].fillna(-1)

    # Fill categorical NAs with 'Unknown' for robustness
    for col in CATEGORICAL_FEATURES:
        X[col] = X[col].fillna('Unknown')

    # 4. Preprocessor
    # CRITICAL: remainder='drop' — never use 'passthrough', which appends
    # extra columns in undefined order and silently corrupts feature alignment.
    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), CATEGORICAL_FEATURES),
            ('num', StandardScaler(), NUMERIC_FEATURES),
        ],
        remainder='drop'  # Explicit: any unlisted column is dropped, not passed through
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    rf = RandomForestClassifier(
        n_estimators=300, class_weight='balanced', random_state=42, n_jobs=-1
    )
    pipeline = Pipeline(steps=[('preprocessor', preprocessor), ('classifier', rf)])

    # 5. Train
    print("Fitting RF...")
    pipeline.fit(X_train, y_train)

    # 6. Evaluate
    y_prob = pipeline.predict_proba(X_test)[:, 1]
    y_pred = pipeline.predict(X_test)
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()

    metrics = {
        "model": "Random Forest",
        "version": f"RF_{MODEL_VERSION}",
        "auc": float(roc_auc_score(y_test, y_prob)),
        "sensitivity": float(recall_score(y_test, y_pred)),
        "npv": float(tn / (tn + fn)) if (tn + fn) > 0 else 0.0,
        "timestamp": datetime.now().isoformat(),
    }
    print(json.dumps(metrics, indent=2))

    # 7. Save versioned artifacts
    pipeline_path = os.path.join(ARTIFACT_DIR, f'mrsa_rf_pipeline_{MODEL_VERSION}.pkl')
    joblib.dump(pipeline, pipeline_path)
    print(f"Saved pipeline to {pipeline_path}")

    # 8. Save feature order lock — single source of truth for inference & SHAP
    feature_lock_path = os.path.join(ARTIFACT_DIR, f'feature_columns_{MODEL_VERSION}.json')
    with open(feature_lock_path, 'w') as f:
        json.dump(FEATURE_COLS, f, indent=2)
    print(f"Saved feature order lock to {feature_lock_path}")

    # 9. Save metrics report
    metrics_path = os.path.join(ARTIFACT_DIR, f'rf_training_report_{MODEL_VERSION}.json')
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)


if __name__ == "__main__":
    train_rf()
