
import numpy as np
import json
import os
import sys
import hashlib
import pickle
import datetime
from xgboost import XGBClassifier
from sklearn.metrics import roc_auc_score, log_loss, confusion_matrix

# Constants
X_TRAIN_PATH = "Processed/ESBL_Stage2_X_train.npy"
Y_TRAIN_PATH = "Processed/ESBL_Stage2_y_train.npy"
X_VAL_PATH = "Processed/ESBL_Stage2_X_val.npy"
Y_VAL_PATH = "Processed/ESBL_Stage2_y_val.npy"
FEATURES_PATH = "Processed/ESBL_Stage2_feature_names.json"
CONFIG_PATH = "Config/esbl_model_config.json"
MODELS_DIR = "Models"
MODEL_FILE = os.path.join(MODELS_DIR, "esbl_xgb_v1.pkl")
METADATA_FILE = os.path.join(MODELS_DIR, "esbl_xgb_v1_metadata.json")

def calculate_file_hash(filepath):
    """Calculates SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def stage4_training():
    print("🔵 STARTING STAGE 4: XGBOOST TRAINING & VALIDATION")
    
    # 1. Load Inputs
    print("Loading Inputs...")
    if not os.path.exists(CONFIG_PATH):
        print(f"❌ Config file missing: {CONFIG_PATH}")
        sys.exit(1)
        
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)
        
    config_hash = calculate_file_hash(CONFIG_PATH)
    print(f"Config Hash (SHA-256): {config_hash[:16]}...")

    X_train = np.load(X_TRAIN_PATH)
    y_train = np.load(Y_TRAIN_PATH)
    X_val = np.load(X_VAL_PATH)
    y_val = np.load(Y_VAL_PATH)
    
    with open(FEATURES_PATH, 'r') as f:
        feature_names = json.load(f)
        
    # 2. Sanity Checks
    print("Running Sanity Checks...")
    if X_train.shape[1] != len(feature_names):
        print(f"❌ Error: Feature count mismatch. X_train: {X_train.shape[1]}, Config: {len(feature_names)}")
        sys.exit(1)
        
    if np.isnan(X_train).any() or np.isnan(X_val).any():
        print("❌ Error: NaNs found in input data.")
        sys.exit(1)
        
    print(f"Train Shape: {X_train.shape}, Val Shape: {X_val.shape}")
    
    # 3. Model Initialization (STRICT)
    print("Initializing Model...")
    # Using ONLY config values for setup, plus deterministic booster settings
    model = XGBClassifier(
        objective=config["objective"],
        eval_metric=config["eval_metric"],
        scale_pos_weight=config["scale_pos_weight"],
        random_state=config["random_state"],
        booster="gbtree", # Locked
        tree_method="hist", # Locked
        # Structural params left at defaults (baseline)
    )
    
    print("Configuration:")
    print(f"  Objective: {config['objective']}")
    print(f"  Scale Pos Weight: {config['scale_pos_weight']}")
    print(f"  Random State: {config['random_state']}")
    print("  Structural Hyperparameters: DEFAULTS (Baseline)")
    
    # 4. Training
    print("Training Model...")
    model.fit(
        X_train, 
        y_train, 
        eval_set=[(X_train, y_train), (X_val, y_val)], 
        verbose=False
    )
    
    # Log Overfitting Signal
    results = model.evals_result()
    train_loss = results['validation_0']['logloss'][-1]
    val_loss = results['validation_1']['logloss'][-1]
    
    print(f"Final Train LogLoss: {train_loss:.4f}")
    print(f"Final Val LogLoss:   {val_loss:.4f}")
    
    # 5. Validation Predictions (Probabilities only)
    print("Generating Validation Predictions...")
    # GUARD: ONLY using predict_proba, NO predict()
    y_val_proba = model.predict_proba(X_val)[:, 1]
    
    # 6. Compute Metrics (Reporting - Default 0.5 threshold)
    print("Computing Baseline Metrics...")
    auroc = roc_auc_score(y_val, y_val_proba)
    loss = log_loss(y_val, y_val_proba)
    
    # Sensitivity/NPV @ 0.5 (Reference only)
    y_val_pred_ref = (y_val_proba >= 0.5).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_val, y_val_pred_ref).ravel()
    
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
    npv = tn / (tn + fn) if (tn + fn) > 0 else 0
    
    print(f"Baseline AUROC:      {auroc:.4f}")
    print(f"Baseline LogLoss:    {loss:.4f}")
    print(f"Ref Sens (@0.5):     {sensitivity:.4f}")
    print(f"Ref NPV (@0.5):      {npv:.4f}")
    
    # 7. Save Artifacts
    print("Saving Artifacts...")
    if not os.path.exists(MODELS_DIR):
        os.makedirs(MODELS_DIR)
        
    # Save Model
    with open(MODEL_FILE, 'wb') as f:
        pickle.dump(model, f)
        
    # Save Metadata
    metadata = {
        "timestamp": datetime.datetime.now().isoformat(),
        "config_hash": config_hash,
        "dataset_info": {
            "train_samples": int(X_train.shape[0]),
            "val_samples": int(X_val.shape[0]),
            "feature_count": int(X_train.shape[1])
        },
        "metrics": {
            "auroc": float(auroc),
            "logloss": float(loss),
            "ref_sensitivity_0.5": float(sensitivity),
            "ref_npv_0.5": float(npv),
            "final_train_loss": float(train_loss),
            "final_val_loss": float(val_loss)
        },
        "model_config": {
            "booster": "gbtree",
            "tree_method": "hist",
            "random_state": config["random_state"]
        }
    }
    
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=4)
        
    print("-" * 30)
    print("✅ STAGE 4 COMPLETED SUCCESSFULLY")
    print(f"Model saved: {MODEL_FILE}")
    print(f"Metadata saved: {METADATA_FILE}")
    print("-" * 30)

if __name__ == "__main__":
    stage4_training()
