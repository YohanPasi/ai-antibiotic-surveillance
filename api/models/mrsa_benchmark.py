import pandas as pd
import numpy as np
import xgboost as xgb
from xgboost import XGBClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold, RandomizedSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, accuracy_score, recall_score, precision_score
from sqlalchemy import create_engine
import joblib
import json
import os
import time

# CONFIG
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ast_user:ast_password_2024@db:5432/ast_db")
ARTIFACT_DIR = "/app/models/mrsa_artifacts"
os.makedirs(ARTIFACT_DIR, exist_ok=True)

def load_and_preprocess():
    print("🔄 Loading Data from DB...")
    engine = create_engine(DATABASE_URL)
    df = pd.read_sql("SELECT * FROM mrsa_raw_clean", engine)
    
    # Drop metadata
    drop_cols = ['id', 'entry_date', 'bht']
    df = df.drop(columns=[c for c in drop_cols if c in df.columns], errors='ignore')

    # Target
    y = df['mrsa_label']
    X = df.drop(columns=['mrsa_label'])

    # Fill Missing
    X['age'] = pd.to_numeric(X['age'], errors='coerce').fillna(X['age'].median())
    
    # Handle growth_time - clean strings like "24h" or "48 h" first if needed, but coerce is strong
    X['growth_time'] = pd.to_numeric(X['growth_time'], errors='coerce')
    X['growth_time'] = X['growth_time'].fillna(X['growth_time'].median())
    
    for c in X.select_dtypes(include=['object']).columns:
        X[c] = X[c].fillna('Unknown')

    # Cell Count Ordinal Encoding
    X['cell_count'] = X['cell_count'].astype(str).str.lower().str.strip()
    cell_map = {
        'none': 0, 'no wc': 0, 'not seen': 0, '0': 0,
        'rare': 1, '+': 1, 'scanty': 1,
        'few': 2, '++': 2,
        'moderate': 3, '+++': 3,
        'many': 4, 'plenty': 4, '++++': 4,
        'unknown': 0
    }
    X['cell_count_encoded'] = X['cell_count'].map(cell_map).fillna(0)
    X = X.drop(columns=['cell_count'])

    # One-Hot Encoding
    X_encoded = pd.get_dummies(X, columns=['ward', 'gender', 'sample_type', 'pus_type', 'gram_positivity'], drop_first=True)
    
    # Save columns for consistency
    with open(os.path.join(ARTIFACT_DIR, "feature_columns.json"), "w") as f:
        json.dump(list(X_encoded.columns), f)
        
    # Scale
    scaler = StandardScaler()
    num_cols = ['age', 'growth_time', 'cell_count_encoded']
    X_encoded[num_cols] = scaler.fit_transform(X_encoded[num_cols])
    
    # Save Scaler (will be overwritten by Champion flow but essential to have)
    joblib.dump(scaler, os.path.join(ARTIFACT_DIR, "scaler.pkl"))

    return X_encoded, y, scaler

def define_models():
    """Defines candidate models and their hyperparameter grids."""
    models = {
        "LogisticRegression": {
            "model": LogisticRegression(max_iter=1000, solver='liblinear'),
            "params": {
                "C": [0.01, 0.1, 1, 10], 
                "penalty": ["l1", "l2"]
            }
        },
        "RandomForest": {
            "model": RandomForestClassifier(random_state=42),
            "params": {
                "n_estimators": [100, 200, 300],
                "max_depth": [5, 10, 20, None],
                "min_samples_split": [2, 5, 10]
            }
        },
        "XGBoost": {
            "model": XGBClassifier(eval_metric="logloss", random_state=42),
            "params": {
                "n_estimators": [100, 300],
                "max_depth": [3, 5, 7],
                "learning_rate": [0.01, 0.05, 0.1],
                "subsample": [0.7, 0.9]
            }
        },
        "GradientBoosting": {
            "model": GradientBoostingClassifier(random_state=42),
            "params": {
                "n_estimators": [100, 200],
                "learning_rate": [0.05, 0.1],
                "max_depth": [3, 5]
            }
        },
        "MLP_NeuralNet": {
            "model": MLPClassifier(max_iter=500, random_state=42),
            "params": {
                "hidden_layer_sizes": [(50,), (100,), (50, 25)],
                "alpha": [0.0001, 0.001],
                "activation": ["relu", "tanh"]
            }
        }
    }
    return models

def run_benchmark():
    print("🧪 Starting MRSA Advanced Benchmarking (Champion/Challenger)...")
    
    X, y, scaler = load_and_preprocess()
    
    # Split Holdout (15%) for final verification
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, stratify=y, random_state=42)
    
    models = define_models()
    leaderboard = []
    
    best_auc = 0
    champion_name = ""
    champion_model = None
    
    for name, config in models.items():
        print(f"\n⚡ Training {name}...")
        start_time = time.time()
        
        # Hyperparameter Tuning with CV
        search = RandomizedSearchCV(
            config["model"], 
            config["params"], 
            n_iter=5, # Keep low for speed in this demo
            cv=StratifiedKFold(n_splits=3), # 3-Fold Stratified
            scoring='roc_auc',
            n_jobs=1, # Avoid interfering with container limits
            random_state=42
        )
        
        search.fit(X_train, y_train)
        best_model = search.best_estimator_
        
        # Evaluate on Holdout
        y_prob = best_model.predict_proba(X_test)[:, 1]
        y_pred = best_model.predict(X_test)
        
        auc = roc_auc_score(y_test, y_prob)
        sens = recall_score(y_test, y_pred)
        spec = recall_score(y_test, y_pred, pos_label=0) # Specificity
        
        elapsed = round(time.time() - start_time, 2)
        
        print(f"   -> AUC: {auc:.4f} | Sens: {sens:.4f} | Spec: {spec:.4f} ({elapsed}s)")
        
        leaderboard.append({
            "model": name,
            "AUC": round(auc, 4),
            "Sensitivity": round(sens, 4),
            "Specificity": round(spec, 4),
            "TrainingTime": elapsed,
            "BestParams": str(search.best_params_)
        })
        
        # Champion Selection Logic
        if auc > best_auc:
            best_auc = auc
            champion_name = name
            champion_model = best_model

    # Save Leaderboard
    lb_df = pd.DataFrame(leaderboard).sort_values(by="AUC", ascending=False)
    print("\n🏆 FINAL LEADERBOARD 🏆")
    print(lb_df[["model", "AUC", "Sensitivity", "Specificity"]])
    
    lb_df.to_json(os.path.join(ARTIFACT_DIR, "benchmark_leaderboard.json"), orient="records", indent=4)
    
    # Save Champion
    print(f"\n🥇 The Champion is: {champion_name} (AUC={best_auc:.4f})")
    
    # Save as the MAIN model (overwriting previous XGBoost default)
    # This automatically upgrades the live API logic.
    joblib.dump(champion_model, os.path.join(ARTIFACT_DIR, "mrsa_xgb_model.pkl"))
    
    # Also save with specific name
    joblib.dump(champion_model, os.path.join(ARTIFACT_DIR, f"mrsa_champion_{champion_name}.pkl"))
    
    print("✅ Benchmarking Complete. Champion model is live.")

if __name__ == "__main__":
    run_benchmark()
