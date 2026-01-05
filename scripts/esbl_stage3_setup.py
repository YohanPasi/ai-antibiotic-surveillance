
import numpy as np
import json
import os
import sys

# Constants
X_TRAIN_PATH = "Processed/ESBL_Stage2_X_train.npy"
Y_TRAIN_PATH = "Processed/ESBL_Stage2_y_train.npy"
FEATURES_PATH = "Processed/ESBL_Stage2_feature_names.json"
CONFIG_DIR = "Config"
CONFIG_FILE = os.path.join(CONFIG_DIR, "esbl_model_config.json")

# Locked Model Bounds
HYPERPARAMS = {
    "max_depth": [3, 6],
    "learning_rate": [0.03, 0.1],
    "n_estimators": [300, 800],
    "subsample": [0.7, 1.0],
    "colsample_bytree": [0.7, 1.0]
}

def stage3_setup():
    print("🔵 STARTING STAGE 3: MODEL SETUP & CONFIGURATION")
    
    # 1. Load Data
    print("Loading Stage 2 outputs...")
    if not (os.path.exists(X_TRAIN_PATH) and os.path.exists(Y_TRAIN_PATH) and os.path.exists(FEATURES_PATH)):
        print("❌ Missing Stage 2 files.")
        sys.exit(1)
        
    X_train = np.load(X_TRAIN_PATH)
    y_train = np.load(Y_TRAIN_PATH)
    with open(FEATURES_PATH, 'r') as f:
        feature_names = json.load(f)
        
    # 2. Verify Label Integrity
    print("Verifying Label Integrity...")
    unique_labels = np.unique(y_train)
    print(f"Unique labels found: {unique_labels}")
    
    if not set(unique_labels).issubset({0, 1}):
        print(f"❌ Error: Invalid labels found. Expected {{0, 1}}, got {unique_labels}")
        sys.exit(1)
        
    print("✅ Labels confirmed: Binary {0, 1}")
    print("ℹ️  CONFIRMATION: Labels are PHENOTYPIC (derived from CTX/CAZ/CRO resistance).")
    print("ℹ️  STATUS: Labels are FINAL. No relabeling will occur.")
    
    # 3. Verify Alignment
    print("Verifying Feature-Label Alignment...")
    if X_train.shape[0] != y_train.shape[0]:
        print(f"❌ Error: X_train rows ({X_train.shape[0]}) != y_train rows ({y_train.shape[0]})")
        sys.exit(1)
        
    if X_train.shape[1] != len(feature_names):
        print(f"❌ Error: X_train cols ({X_train.shape[1]}) != feature names count ({len(feature_names)})")
        sys.exit(1)
        
    print(f"✅ Alignment Check Passed: {X_train.shape[0]} samples, {X_train.shape[1]} features")
    
    # 4. Calculate Class Imbalance
    print("Calculating Class Imbalance Parameters...")
    n_pos = np.sum(y_train == 1)
    n_neg = np.sum(y_train == 0)
    total = len(y_train)
    
    print(f"Positives (ESBL+): {n_pos} ({n_pos/total:.2%})")
    print(f"Negatives (ESBL-): {n_neg} ({n_neg/total:.2%})")
    
    if n_pos == 0 or n_neg == 0:
        print("❌ Error: Zero count for one class.")
        sys.exit(1)
        
    scale_pos_weight = n_neg / n_pos
    print(f"✅ Calculated scale_pos_weight: {scale_pos_weight:.4f}")
    
    # 5. Define Model Config
    print("Defining Model Config...")
    config = {
        "model_type": "XGBoostClassifier",
        "objective": "binary:logistic",
        "eval_metric": "logloss",
        "random_state": 42, # FIXED for reproducibility
        "scale_pos_weight": float(scale_pos_weight),
        "hyperparameter_bounds": HYPERPARAMS,
        "metric_priority": ["NPV", "Sensitivity", "AUROC"],
        "feature_count": len(feature_names),
        "feature_names_path": FEATURES_PATH,
        "label_definition": "Phenotypic (CTX/CAZ/CRO) - FINAL"
    }
    
    # 6. Enforce No Training
    print("🛡️  GUARD: No training will be performed in this stage.")
    
    # 7. Save Config
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
        
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)
        
    print("-" * 30)
    print("✅ STAGE 3 COMPLETED SUCCESSFULLY")
    print(f"Configuration saved to: {CONFIG_FILE}")
    print("Exiting without training.")
    print("-" * 30)

if __name__ == "__main__":
    stage3_setup()
