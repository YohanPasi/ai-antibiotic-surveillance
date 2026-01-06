
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
MODEL_FILE = os.path.join(MODELS_DIR, "esbl_xgb_early_v1.pkl")
METADATA_FILE = os.path.join(MODELS_DIR, "esbl_xgb_early_v1_metadata.json")

EXCLUDED_FEATURES = ["CTX", "CAZ", "CRO"]

def calculate_file_hash(filepath):
    """Calculates SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def stage5_early_model():
    print("🔵 STARTING STAGE 5: EARLY ESBL RISK PREDICTION MODEL")
    
    # 1. Load Inputs (Same as Stage 4)
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
        
    print(f"Original Train Shape: {X_train.shape}, Val Shape: {X_val.shape}")
    
    # 3. Define Exclusions
    print(f"Defining Exclusions: {EXCLUDED_FEATURES}")
    print("ℹ️  LABEL DEFINITION: Phenotypic ESBL (CTX/CAZ/CRO) – unchanged from Stage 1.")
    
    # 4. Feature Masking
    print("Masking Features...")
    keep_indices = []
    early_feature_names = []
    
    for i, name in enumerate(feature_names):
        # Check if the feature name exactly matches or contains the excluded antibiotic code
        # Assumption: Feature names are preserved from Stage 2.
        # Strict match or substring? Stage 2 one-hot encoded categorical.
        # But CTX/CAZ/CRO are BINARY columns, not categorical, so they should be exact matches in feature_names.
        if name in EXCLUDED_FEATURES:
            print(f"  Filtering out: {name}")
        else:
            keep_indices.append(i)
            early_feature_names.append(name)
            
    if len(keep_indices) == len(feature_names):
        print("⚠️ WARNING: No features were excluded. Check feature names.")
        # We might have suffixes if something changed, but Stage 2 said Binary features are kept as is.
        # Let's verify if they exist.
        
    # Apply Mask
    X_train_early = X_train[:, keep_indices]
    X_val_early = X_val[:, keep_indices]
    
    print(f"Feature Count Reduced: {len(feature_names)} -> {len(early_feature_names)}")
    
    # 5. Post-Mask Alignment Check
    print("Verifying Post-Mask Alignment...")
    if X_train_early.shape[0] != y_train.shape[0]:
        print("❌ Error: Train rows mismatch after masking.")
        sys.exit(1)
        
    if X_val_early.shape[0] != y_val.shape[0]:
        print("❌ Error: Val rows mismatch after masking.")
        sys.exit(1)
        
    print("✅ Alignment Verified.")
    
    # 6. Initialize Model
    print("Initializing Model...")
    model = XGBClassifier(
        objective=config["objective"],
        eval_metric=config["eval_metric"],
        scale_pos_weight=config["scale_pos_weight"],
        random_state=config["random_state"],
        booster="gbtree", 
        tree_method="hist", 
    )
    
    print("Configuration: (Same as Stage 4)")
    print(f"  Objective: {config['objective']}")
    print(f"  Scale Pos Weight: {config['scale_pos_weight']}")
    
    # 7. Train Early Model
    print("Training Early Model...")
    model.fit(
        X_train_early, 
        y_train, 
        eval_set=[(X_train_early, y_train), (X_val_early, y_val)], 
        verbose=False
    )
    
    # Log Overfitting Signal
    results = model.evals_result()
    train_loss = results['validation_0']['logloss'][-1]
    val_loss = results['validation_1']['logloss'][-1]
    
    print(f"Final Train LogLoss: {train_loss:.4f}")
    print(f"Final Val LogLoss:   {val_loss:.4f}")
    
    # 8. Validation Predictions (Probabilities only)
    print("Generating Validation Predictions...")
    # GUARD: ONLY using predict_proba, NO predict()
    y_val_proba_early = model.predict_proba(X_val_early)[:, 1]
    
    # 9. Compute Metrics (Reporting)
    print("Computing Early Metrics...")
    auroc = roc_auc_score(y_val, y_val_proba_early)
    loss = log_loss(y_val, y_val_proba_early)
    
    # Sensitivity/NPV @ 0.5 (Reference only)
    y_val_pred_ref = (y_val_proba_early >= 0.5).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_val, y_val_pred_ref).ravel()
    
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
    npv = tn / (tn + fn) if (tn + fn) > 0 else 0
    
    print(f"Early Model AUROC:      {auroc:.4f}")
    print(f"Early Model LogLoss:    {loss:.4f}")
    print(f"Ref Sens (@0.5):        {sensitivity:.4f}")
    print(f"Ref NPV (@0.5):         {npv:.4f}")
    
    if auroc >= 0.999:
        print("⚠️ WARNING: AUROC is still ~1.0. Check if leakage exists!")
    
    # 10. Save Artifacts
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
        "model_variant": "EARLY_ESBL_RISK",
        "label_definition": "Phenotypic ESBL (CTX/CAZ/CRO) – unchanged",
        "clinical_note": "Risk prediction only; not a diagnostic confirmation",
        "excluded_features": EXCLUDED_FEATURES,
        "dataset_info": {
            "train_samples": int(X_train.shape[0]),
            "val_samples": int(X_val.shape[0]),
            "feature_count_original": int(X_train.shape[1]),
            "feature_count_used": int(X_train_early.shape[1])
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
    print("✅ STAGE 5 COMPLETED SUCCESSFULLY")
    print(f"Model saved: {MODEL_FILE}")
    print(f"Metadata saved: {METADATA_FILE}")
    print("-" * 30)

if __name__ == "__main__":
    stage5_early_model()
