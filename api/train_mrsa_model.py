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
from sklearn.metrics import roc_auc_score, confusion_matrix, recall_score, precision_score, classification_report

# Supabase Connection
DATABASE_URL = "postgresql://postgres.zdhvyhijuriggezelyxq:Yohan%26pasi80253327@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres?sslmode=require"

ARTIFACT_DIR = r'd:\Yohan\Project\api\models\mrsa_artifacts'
os.makedirs(ARTIFACT_DIR, exist_ok=True)

def train_model():
    print("Starting MRSA Model Training (Stage B)...")
    
    # 1. Load Data
    print("Connecting to Supabase...")
    engine = create_engine(DATABASE_URL)
    query = "SELECT * FROM mrsa_raw_clean"
    df = pd.read_sql(query, engine)
    
    print(f"Loaded {len(df)} records.")
    
    # 2. Split Features & Label
    # Exclude audit columns: id, bht, original_timestamp, entry_date
    feature_cols = ['age', 'gender', 'ward', 'sample_type', 
                   'pus_type', 'cell_count', 'gram_positivity', 'growth_time']
    
    X = df[feature_cols].copy()
    y = df['mrsa_label'].values
    
    # 3. Preprocessing Setup
    # Imputation (Basic handling for training)
    X['age'] = X['age'].fillna(X['age'].median())
    X['growth_time'] = X['growth_time'].fillna(X['growth_time'].median())
    for col in ['gender', 'ward', 'sample_type', 'pus_type', 'gram_positivity']:
        X[col] = X[col].fillna('Unknown')
    
    # Define Transformers
    categorical_features = ['ward', 'sample_type', 'pus_type', 'gram_positivity', 'gender']
    numeric_features = ['age', 'growth_time']
    # cell_count is ordinal preserved as is
    
    # Create Preprocessor
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features)
        ],
        remainder='passthrough' # Keep cell_count
    )
    
    # 4. Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )
    
    # 5. Pipeline & Training
    print("Training Random Forest...")
    rf = RandomForestClassifier(
        n_estimators=300,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )
    
    # Fit Pipeline
    pipeline = Pipeline(steps=[('preprocessor', preprocessor), ('classifier', rf)])
    pipeline.fit(X_train, y_train)
    
    # 6. Evaluation
    print("Evaluating...")
    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1]
    
    auc = roc_auc_score(y_test, y_prob)
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
    sensitivity = recall_score(y_test, y_pred) # Recall of positive class
    specificity = tn / (tn + fp)
    npv = tn / (tn + fn) if (tn + fn) > 0 else 0
    
    metrics = {
        "model_version": "RF_v1",
        "training_date": datetime.now().isoformat(),
        "row_count": len(df),
        "mrsa_prevalence": float(y.mean()),
        "auc": float(auc),
        "sensitivity": float(sensitivity),
        "specificity": float(specificity),
        "npv": float(npv),
        "accuracy": float((tp + tn) / len(y_test))
    }
    
    print("\n--- Training Report ---")
    print(json.dumps(metrics, indent=2))
    
    # 7. Feature Importance & Columns
    # Extract feature names AFTER encoding
    ohe_feature_names = pipeline.named_steps['preprocessor'].named_transformers_['cat'].get_feature_names_out(categorical_features)
    all_feature_names = numeric_features + list(ohe_feature_names) + ['cell_count'] # Remainder is at end usually
    
    importances = pipeline.named_steps['classifier'].feature_importances_
    feat_importance = sorted(zip(all_feature_names, importances), key=lambda x: x[1], reverse=True)
    
    # 8. Save Artifacts
    print(f"\nSaving artifacts to {ARTIFACT_DIR}...")
    
    # Save Model (Pipeline allows raw input prediction, but we usually save parts for flexibility)
    # Strategy: Save the whole pipeline for easiest inference
    joblib.dump(pipeline, os.path.join(ARTIFACT_DIR, 'mrsa_rf_pipeline.pkl'))
    
    # Also save components separately if needed for explicit step-by-step
    joblib.dump(rf, os.path.join(ARTIFACT_DIR, 'mrsa_rf_model.pkl'))
    joblib.dump(pipeline.named_steps['preprocessor'], os.path.join(ARTIFACT_DIR, 'mrsa_preprocessor.pkl'))
    
    # Save Metadata
    with open(os.path.join(ARTIFACT_DIR, 'training_report.json'), 'w') as f:
        json.dump(metrics, f, indent=2)
        
    with open(os.path.join(ARTIFACT_DIR, 'feature_columns.json'), 'w') as f:
        json.dump(all_feature_names, f, indent=2)
        
    with open(os.path.join(ARTIFACT_DIR, 'feature_importance.json'), 'w') as f:
        json.dump([{"feature": f, "importance": float(i)} for f, i in feat_importance], f, indent=2)
        
    print("Stage B Complete. Model Trained & Frozen.")

if __name__ == "__main__":
    train_model()
