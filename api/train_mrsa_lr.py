import pandas as pd
import numpy as np
import joblib
import json
import os
from datetime import datetime
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score, recall_score

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "postgresql://postgres.zdhvyhijuriggezelyxq:Yohan%26pasi80253327@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres?sslmode=require"

ARTIFACT_DIR = r'/app/models/mrsa_artifacts'
if os.name == 'nt':
    ARTIFACT_DIR = r'd:\Yohan\Project\api\models\mrsa_artifacts'
os.makedirs(ARTIFACT_DIR, exist_ok=True)

def train_lr():
    print("Starting Logistic Regression Training (Baseline)...")
    
    engine = create_engine(DATABASE_URL)
    df = pd.read_sql("SELECT * FROM mrsa_raw_clean", engine)
    
    feature_cols = ['age', 'gender', 'ward', 'sample_type', 
                   'pus_type', 'cell_count', 'gram_positivity', 'growth_time']
    X = df[feature_cols].copy()
    y = df['mrsa_label'].values
    
    X['age'] = X['age'].fillna(X['age'].median())
    X['growth_time'] = X['growth_time'].fillna(X['growth_time'].median())
    for col in ['gender', 'ward', 'sample_type', 'pus_type', 'gram_positivity']:
        X[col] = X[col].fillna('Unknown')
        
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), ['age', 'growth_time']),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), ['ward', 'sample_type', 'pus_type', 'gram_positivity', 'gender'])
        ],
        remainder='passthrough'
    )
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
    
    lr = LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42)
    pipeline = Pipeline(steps=[('preprocessor', preprocessor), ('classifier', lr)])
    
    print("Fitting LR...")
    pipeline.fit(X_train, y_train)
    
    y_prob = pipeline.predict_proba(X_test)[:, 1]
    y_pred = pipeline.predict(X_test)
    
    metrics = {
        "model": "Logistic Regression",
        "version": "LR_v1",
        "auc": float(roc_auc_score(y_test, y_prob)),
        "sensitivity": float(recall_score(y_test, y_pred)),
        "timestamp": datetime.now().isoformat()
    }
    print(json.dumps(metrics, indent=2))
    
    path = os.path.join(ARTIFACT_DIR, 'mrsa_lr_pipeline.pkl')
    joblib.dump(pipeline, path)
    print(f"Saved to {path}")

if __name__ == "__main__":
    train_lr()
