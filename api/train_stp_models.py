import os
import sys
import json
import uuid
import joblib
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from xgboost import XGBClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, brier_score_loss

# Configuration
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres.zdhvyhijuriggezelyxq:Yohan%26pasi80253327@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

MODEL_PATH = os.path.join(MODELS_DIR, "stp_xgb_v1.pkl")

def get_engine():
    return create_engine(DATABASE_URL)

def seed_synthetic_features(engine):
    print("Seeding synthetic STP features since DB table is empty...")
    wards = ['ICU', 'Surgical Ward A', 'Medical Ward A']
    organisms = ['Streptococcus pneumoniae', 'Enterococcus faecalis']
    antibiotics = ['Penicillin', 'Vancomycin', 'Linezolid']
    
    rows = []
    # Start exactly 52 weeks ago, aligned to start of week (Monday)
    base_date = pd.to_datetime(datetime.now().date()) - pd.Timedelta(weeks=52)
    base_date = base_date - pd.Timedelta(days=base_date.weekday())
    
    for w in wards:
        for o in organisms:
            for a in antibiotics:
                for i in range(53):
                    week_start = base_date + pd.Timedelta(weeks=i)
                    RR = np.random.uniform(0.1, 0.6)
                    
                    # Create an outbreak for Vancomycin in ICU recently
                    if w == 'ICU' and o == 'Enterococcus faecalis' and a == 'Vancomycin' and i > 40:
                        RR = min(1.0, RR + np.random.uniform(0.2, 0.4))
                        
                    rows.append({
                        'ward': w,
                        'organism': o,
                        'antibiotic': a,
                        'week_start': week_start,
                        'resistance_rate': RR,
                        'tested_count': np.random.randint(15, 60),
                        'trend_slope': np.random.uniform(-0.1, 0.2), # rolling_slope
                        'volatility': np.random.uniform(0.01, 0.1),
                        'exposure_density': np.random.uniform(10, 50),
                        'shannon_index': np.random.uniform(1.0, 3.0),
                        'is_stable': True,
                        'is_partial_window': False,
                        'stage2_version': 'v2-synth',
                        'derived_from_stage1_version': 'v1-synth',
                        'is_frozen': True
                    })
    
    df = pd.DataFrame(rows)
    df.to_sql('stp_stage2_feature_store', engine, if_exists='append', index=False)
    print(f"Seeded {len(df)} synthetic feature rows.")
    return df

def load_data(engine):
    print("Extracting features from stp_stage2_feature_store...")
    df = pd.read_sql("SELECT * FROM stp_stage2_feature_store", engine)
    
    if len(df) < 50:
        seed_synthetic_features(engine)
        df = pd.read_sql("SELECT * FROM stp_stage2_feature_store", engine)
        
    return df

def build_labels(df):
    print("Generating T+1 target labels (M31)...")
    df['week_start'] = pd.to_datetime(df['week_start'])
    df = df.sort_values(by=['ward', 'organism', 'antibiotic', 'week_start'])
    
    # Next week's resistance rate
    df['future_rate'] = df.groupby(['ward', 'organism', 'antibiotic'])['resistance_rate'].shift(-1)
    
    # Train set (we have future rate)
    train_df = df.dropna(subset=['future_rate']).copy()
    
    # Label: e.g. >= 0.30 resistance rate is "High Risk"
    train_df['label'] = (train_df['future_rate'] >= 0.30).astype(int)
    
    return train_df

def run_training_pipeline():
    print("="*60)
    print(" STP AUTOMATED RETRAINING PIPELINE TRIGGERED")
    print("="*60)
    
    engine = get_engine()
    df = load_data(engine)
    
    train_df = build_labels(df)
    
    features = ['resistance_rate', 'tested_count', 'trend_slope', 'volatility', 'exposure_density', 'shannon_index']
    
    # Fill NAs
    X = train_df[features].fillna(0).copy()
    y = train_df['label']
    
    print(f"Training XGBoost on {len(X)} historical records...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    
    base_xgb = XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.05, eval_metric='logloss')
    clf = CalibratedClassifierCV(estimator=base_xgb, method='sigmoid', cv=3)
    
    clf.fit(X_train, y_train)
    
    probs = clf.predict_proba(X_test)[:, 1]
    
    auc = roc_auc_score(y_test, probs) if len(y_test.unique()) > 1 else 0.5
    brier = brier_score_loss(y_test, probs)
    
    print(f"Metrics -> AUC: {auc:.3f}, Brier: {brier:.3f}")
    
    metrics = {"AUC": float(auc), "Brier": float(brier), "samples": len(X)}
    
    print("Saving Models and registering in DB...")
    bundle = {
        "model": clf,
        "features": features
    }
    
    joblib.dump(bundle, MODEL_PATH)
    
    model_id = str(uuid.uuid4())
    
    with engine.begin() as conn:
        # Deactivate old models
        conn.execute(text("UPDATE stp_model_registry SET status = 'archived' WHERE status IN ('active', 'shadow')"))
        
        # Insert new
        conn.execute(text("""
            INSERT INTO stp_model_registry 
            (model_id, model_type, target, horizon, features_hash, stage2_version, status, filepath, metrics_json, created_at)
            VALUES (:id, 'xgboost', 'resistance_rate', 1, 'v1-hash', 'v2-synth', 'active', :filepath, :metrics, :created)
        """), {
            "id": model_id,
            "filepath": "models/stp_xgb_v1.pkl",
            "metrics": json.dumps(metrics),
            "created": datetime.now()
        })
        
    print(f"✅ RETRAINING PIPELINE COMPLETED SUCCESSFULLY. New Model ID: {model_id}")

if __name__ == "__main__":
    run_training_pipeline()
