import os
import json
import pickle
import datetime
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score, brier_score_loss, roc_curve

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DATA_PATH = os.path.join(os.path.dirname(BASE_DIR), "Raw", "ESBL_Training_Dataset_Final_12000rows.xlsx")
MODELS_DIR = os.path.join(BASE_DIR, "models")
CONFIG_DIR = os.path.join(BASE_DIR, "config")
MODEL_PATH = os.path.join(MODELS_DIR, "beta_lactam_xgb_v2.pkl")
META_PATH = os.path.join(CONFIG_DIR, "beta_lactam_model_meta.json")
THRESHOLDS_PATH = os.path.join(CONFIG_DIR, "beta_lactam_thresholds.json")
EVIDENCE_PATH = os.path.join(CONFIG_DIR, "beta_lactam_outcome_tables.json")
FEATURES_PATH = os.path.join(CONFIG_DIR, "beta_lactam_features.json")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(CONFIG_DIR, exist_ok=True)

TARGET_MAP = {
    "Gen1": "AMP",
    "Gen2": "CXM",
    "Gen3": "CTX",
    "BL_Combo": "AMC"
}

def preprocess_data(df):
    print("Preprocessing data...")
    # Derive Severity Proxy
    df['Severity'] = df['Ward'].apply(lambda x: 'High' if str(x).upper() == 'ICU' else 'Normal')
    
    # Sample Grouping
    invasive_samples = ['Blood', 'CSF']
    df['Sample_Group'] = df['Sample_Type'].apply(lambda x: 'Invasive' if x in invasive_samples else 'Non-Invasive')
    
    # Age Binning
    df['Age_Bin'] = pd.cut(df['Age'], bins=[-1, 18, 40, 65, 120], labels=['0-18', '19-40', '41-65', '66+'])
    df['Age_Bin'] = df['Age_Bin'].astype(str)
    
    # Extract Targets
    y_dict = {}
    for gen, col in TARGET_MAP.items():
        if col in df.columns:
            y_dict[gen] = df[col].values
        else:
            print(f"Warning: Target column {col} missing.")
            
    # Drop all AST Leakage Columns
    ast_columns = ['AMP', 'CXM', 'CTX', 'CAZ', 'CRO', 'CIP', 'CN', 'AMC', 'TZP', 'ESBL_Label']
    df_features = df.drop(columns=[col for col in ast_columns if col in df.columns])
    
    # Drop IDs and Dates
    df_features = df_features.drop(columns=['Lab_No', 'Sample_Date', 'PUS_Type', 'Pure_Growth', 'Growth_Time_After', 'Gram_Result'], errors='ignore')
    
    # Convert categorical to string to handle 'Unknown' / fallback
    for col in df_features.columns:
        if df_features[col].dtype == 'object' or df_features[col].dtype.name == 'category':
            df_features[col] = df_features[col].fillna('Unknown').astype(str)
        else:
            df_features[col] = df_features[col].fillna(df_features[col].median())
            
    # One-Hot Encoding
    X = pd.get_dummies(df_features, dummy_na=True)
    feature_names = list(X.columns)
    
    return X.values, y_dict, feature_names

def find_youden_threshold(y_true, y_prob):
    fpr, tpr, thresholds = roc_curve(y_true, y_prob)
    j_scores = tpr - fpr
    best_idx = np.argmax(j_scores)
    best_threshold = thresholds[best_idx]
    return float(best_threshold)

def generate_evidence_tables(y_dict):
    tables = {}
    alpha = 2 # Laplace smoothing
    for gen, y in y_dict.items():
        success = int(np.sum(y == 1))
        total = len(y)
        p = (success + alpha) / (total + 2 * alpha)
        tables[gen] = {
            "success": success,
            "total": total,
            "baseline_prob": round(p, 4)
        }
    return tables

def train_and_evaluate():
    print("Loading Dataset...")
    df = pd.read_excel(RAW_DATA_PATH)
    total_rows = len(df)
    
    X_full, y_dict, feature_names = preprocess_data(df)
    
    models = {}
    metrics = {}
    thresholds = {}
    
    print(f"Dataset shape: {X_full.shape}")
    
    for gen, y_full in y_dict.items():
        print(f"\\n--- Training {gen} ---")
        # Ensure binary targets
        y_full = np.where(y_full > 0, 1, 0)
        
        # Check for single-class target
        if len(np.unique(y_full)) < 2:
            print(f"Target {gen} has only 1 unique class ({y_full[0]}). Using DummyClassifier.")
            from sklearn.dummy import DummyClassifier
            dummy = DummyClassifier(strategy="constant", constant=y_full[0])
            # Train-Test Split just to maintain array shapes
            X_train, X_test, y_train, y_test = train_test_split(X_full, y_full, test_size=0.2, random_state=42)
            dummy.fit(X_train, y_train)
            
            y_prob = dummy.predict_proba(X_test)[:, 1] if dummy.predict_proba(X_test).shape[1] > 1 else np.ones(len(X_test)) * y_full[0]
            best_thresh = 0.5
            auroc, prec, rec, f1, brier = 0.5, 0.0, 0.0, 0.0, 0.0
            
            metrics[gen] = {
                "AUROC": float(auroc),
                "Precision": float(prec),
                "Recall": float(rec),
                "F1_Score": float(f1),
                "Brier_Score": float(brier),
                "Optimal_Threshold": float(best_thresh)
            }
            
            thresholds[gen] = {
                "decision_threshold": float(best_thresh),
                "traffic_lights": {
                    "green_min": 0.75,
                    "amber_min": 0.45
                }
            }
            models[gen] = dummy
            continue

        # Train-Test Split (Nested Evaluation)
        X_train, X_test, y_train, y_test = train_test_split(X_full, y_full, test_size=0.2, random_state=42, stratify=y_full)
        
        # Calculate Scale Pos Weight for class imbalance
        neg_count = np.sum(y_train == 0)
        pos_count = np.sum(y_train == 1)
        scale_weight = neg_count / pos_count if pos_count > 0 else 1.0
        
        # Base Model
        base_xgb = XGBClassifier(
            n_estimators=150,
            max_depth=5,
            learning_rate=0.05,
            objective="binary:logistic",
            eval_metric="logloss",
            scale_pos_weight=scale_weight,
            random_state=42,
            n_jobs=-1
        )
        
        # Nested Calibration with 3-fold internal CV
        print(f"Calibrating {gen} with Isotonic Regression...")
        calibrated_model = CalibratedClassifierCV(base_xgb, method='isotonic', cv=3)
        calibrated_model.fit(X_train, y_train)
        
        # Predictions on Held-out Test Set
        y_prob = calibrated_model.predict_proba(X_test)[:, 1]
        
        # Optimal Threshold
        best_thresh = find_youden_threshold(y_test, y_prob)
        y_pred = (y_prob >= best_thresh).astype(int)
        
        # Metrics
        try:
            auroc = roc_auc_score(y_test, y_prob)
        except ValueError:
            auroc = 0.5
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        brier = brier_score_loss(y_test, y_prob)
        
        print(f"AUROC: {auroc:.4f} | Brier: {brier:.4f} | Threshold: {best_thresh:.4f}")
        
        metrics[gen] = {
            "AUROC": float(auroc),
            "Precision": float(prec),
            "Recall": float(rec),
            "F1_Score": float(f1),
            "Brier_Score": float(brier),
            "Optimal_Threshold": float(best_thresh)
        }
        
        # Define Interpretability Bands dynamically based on threshold
        green_min = min(0.95, best_thresh + 0.15)
        amber_min = max(0.10, best_thresh - 0.15)
        
        thresholds[gen] = {
            "decision_threshold": float(best_thresh),
            "traffic_lights": {
                "green_min": float(green_min),
                "amber_min": float(amber_min)
            }
        }
        
        models[gen] = calibrated_model
        
    print("\\nSaving Artifacts...")
    
    # 1. Model Dictionary
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(models, f)
        
    # 2. Metadata & Metrics
    meta = {
        "model_version": "v2_2026_05_03",
        "training_rows": total_rows,
        "features_used": len(feature_names),
        "training_timestamp": datetime.datetime.now().isoformat(),
        "metrics": metrics
    }
    with open(META_PATH, "w") as f:
        json.dump(meta, f, indent=4)
        
    # 3. Thresholds
    with open(THRESHOLDS_PATH, "w") as f:
        json.dump(thresholds, f, indent=4)
        
    # 4. Evidence Tables
    evidence = generate_evidence_tables(y_dict)
    with open(EVIDENCE_PATH, "w") as f:
        json.dump(evidence, f, indent=4)
        
    # 5. Features Definition
    # We save exactly what the model expects, so the inference can build it
    # We will need the mapping categories for inference
    feature_config = {
        "one_hot_columns": feature_names,
        "required_features": ['Age', 'Gender', 'Ward', 'Organism', 'Sample_Type', 'Cell_Count_Level']
    }
    with open(FEATURES_PATH, "w") as f:
        json.dump(feature_config, f, indent=4)
        
    print("[SUCCESS] Training Pipeline Completed Successfully.")

if __name__ == "__main__":
    train_and_evaluate()
