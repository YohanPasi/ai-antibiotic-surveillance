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

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Fallback/Default for local testing if env not set
    DATABASE_URL = "postgresql://postgres.zdhvyhijuriggezelyxq:Yohan%26pasi80253327@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres?sslmode=require"

ARTIFACT_DIR = r'/app/models/mrsa_artifacts' # Container path
if os.name == 'nt':
    ARTIFACT_DIR = r'd:\Yohan\Project\api\models\mrsa_artifacts'

os.makedirs(ARTIFACT_DIR, exist_ok=True)

def train_rf():
    print("Starting Random Forest Training (Champion)...")
    
    # 1. Load Data
    engine = create_engine(DATABASE_URL)
    query = "SELECT * FROM mrsa_raw_clean"
    df = pd.read_sql(query, engine)
    print(f"Loaded {len(df)} records.")
    
    # 2. Split
    feature_cols = ['age', 'gender', 'ward', 'sample_type', 
                   'pus_type', 'cell_count', 'gram_positivity', 'growth_time']
    X = df[feature_cols].copy()
    y = df['mrsa_label'].values
    
    # 3. Impute
    X['age'] = X['age'].fillna(X['age'].median())
    X['growth_time'] = X['growth_time'].fillna(X['growth_time'].median())
    for col in ['gender', 'ward', 'sample_type', 'pus_type', 'gram_positivity']:
        X[col] = X[col].fillna('Unknown')
        
    # 4. Pipeline
    categorical_features = ['ward', 'sample_type', 'pus_type', 'gram_positivity', 'gender']
    numeric_features = ['age', 'growth_time']
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features)
        ],
        remainder='passthrough'
    )
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
    
    rf = RandomForestClassifier(n_estimators=300, class_weight='balanced', random_state=42, n_jobs=-1)
    pipeline = Pipeline(steps=[('preprocessor', preprocessor), ('classifier', rf)])
    
    # 5. Train
    print("Fitting RF...")
    pipeline.fit(X_train, y_train)
    
    # 6. Evaluate
    y_prob = pipeline.predict_proba(X_test)[:, 1]
    y_pred = pipeline.predict(X_test)
    
    metrics = {
        "model": "Random Forest",
        "version": "RF_v1",
        "auc": float(roc_auc_score(y_test, y_prob)),
        "sensitivity": float(recall_score(y_test, y_pred)),
        "timestamp": datetime.now().isoformat()
    }
    print(json.dumps(metrics, indent=2))
    
    # 7. Save
    path = os.path.join(ARTIFACT_DIR, 'mrsa_rf_pipeline.pkl')
    joblib.dump(pipeline, path)
    print(f"Saved to {path}")

if __name__ == "__main__":
    train_rf()
