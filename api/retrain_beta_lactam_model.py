import os
import sys
import json
import shutil
import pickle
import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy import create_engine
from xgboost import XGBClassifier
from sklearn.multioutput import MultiOutputClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import classification_report, roc_auc_score, brier_score_loss, confusion_matrix

# Configuration
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "postgresql://postgres.zdhvyhijuriggezelyxq:Yohan%26pasi80253327@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
CONFIG_DIR = os.path.join(BASE_DIR, "config")
BACKUP_DIR = os.path.join(MODELS_DIR, "backups")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# Artifact Paths
MODEL_PATH = os.path.join(MODELS_DIR, "beta_lactam_xgb_v2.pkl")
THRESHOLDS_PATH = os.path.join(CONFIG_DIR, "beta_lactam_thresholds.json")
EVIDENCE_PATH = os.path.join(CONFIG_DIR, "beta_lactam_outcome_tables.json")
META_PATH = os.path.join(CONFIG_DIR, "beta_lactam_model_meta.json")
FEATURES_PATH = os.path.join(CONFIG_DIR, "beta_lactam_features.json")
AUDIT_LOG_CSV = os.path.join(CONFIG_DIR, "retraining_audit_log.csv")

TARGETS = ["Gen1", "Gen2", "Gen3", "Gen4", "Carbapenem", "BL_Combo"]
NUMERIC_FEATURES = ["Age"]
CATEGORICAL_FEATURES = ["Gender", "Ward", "Organism", "Sample_Type", "Cell_Count_Level"]


def connect_db():
    print(f"Connecting to DB...")
    return create_engine(DATABASE_URL)


def backup_old_artifacts():
    print("Backing up existing artifacts...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for file_path in [
        os.path.join(MODELS_DIR, "beta_lactam_xgb_v1.pkl"),
        os.path.join(MODELS_DIR, "beta_lactam_xgb_v2.pkl"),
        THRESHOLDS_PATH, EVIDENCE_PATH, META_PATH, FEATURES_PATH
    ]:
        if os.path.exists(file_path):
            filename = os.path.basename(file_path)
            backup_path = os.path.join(BACKUP_DIR, f"{timestamp}_{filename}")
            shutil.copy2(file_path, backup_path)


def load_data(engine):
    print("Extracting Day-0 Encounters and Day-3 Lab Results...")
    
    # Extract patient encounters
    query_encounters = "SELECT encounter_id, age, gender, ward, sample_type, organism, cell_count_level FROM beta_lactam_encounters"
    df_encounters = pd.read_sql(query_encounters, engine)
    
    # Extract laboratory AST results using the pre-calculated generation column
    query_labs = """
    SELECT encounter_id, result as ast_result, generation 
    FROM beta_lactam_lab_results
    WHERE generation IN ('Gen1', 'Gen2', 'Gen3', 'Gen4', 'Carbapenem', 'BL_Combo')
    """
    df_labs = pd.read_sql(query_labs, engine)
    
    if len(df_encounters) == 0 or len(df_labs) == 0:
        raise ValueError("Insufficient data in database to perform retraining.")

    # Pivot AST results so each encounter has a row with all 6 target generations
    # We take the worst-case (min) if multiple antibiotics of the same generation exist.
    # S=1, (I, R)=0
    df_labs['outcome'] = df_labs['ast_result'].apply(lambda x: 1 if x == 'S' else 0)
    pivot_labs = df_labs.groupby(['encounter_id', 'generation'])['outcome'].min().unstack(fill_value=np.nan)
    
    # Merge Features (Encounters) + Targets (Pivoted Labs)
    df = df_encounters.merge(pivot_labs, on='encounter_id', how='inner')
    
    # Drop rows where ALL 6 generations are missing (should not happen, but safe to filter)
    df = df.dropna(subset=TARGETS, how='all')

    print(f"Extracted {len(df)} matched patient encounters with AST data.")
    return df


def preprocess_data(df):
    print("Preprocessing Features...")
    # Missing values imputation
    df['Age'] = pd.to_numeric(df['age'], errors='coerce')
    df['Age'].fillna(df['Age'].median(), inplace=True)
    
    for col in CATEGORICAL_FEATURES:
        col_lower = col.lower()
        if col_lower in df.columns:
            df[col] = df[col_lower].fillna("Unknown")

    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES].copy()
    
    # Targets: Fill missing generation AST using a conservative approach 
    # (if Gen1S -> Gen3S usually, but for safe training, fill NA with -1 and handle via sample_weight)
    Y = df[TARGETS].copy()
    Y.fillna(0, inplace=True) # Binary classification S=1, I/R=0
    
    # Setup transformer
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', 'passthrough', NUMERIC_FEATURES),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), CATEGORICAL_FEATURES)
        ])
    
    X_encoded = preprocessor.fit_transform(X)
    
    # Extract encoded feature names
    cat_feature_names = preprocessor.named_transformers_['cat'].get_feature_names_out(CATEGORICAL_FEATURES)
    feature_names = NUMERIC_FEATURES + list(cat_feature_names)
    
    return X_encoded, Y.values, feature_names, preprocessor


def train_model(X, Y, feature_names):
    print("Training XGBoost MultiOutput Classifier...")
    
    # 80/20 train/test split
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=42)
    
    # Base Estimator
    base_xgb = XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.05,
        objective="binary:logistic",
        eval_metric="logloss",
        n_jobs=-1,
        random_state=42
    )

    # Use CalibratedClassifierCV to ensure output probabilities are reliable (Platt scaling via sigmoid)
    # We wrap it in MultiOutputClassifier.
    # Fallback to base classifier if the dataset is too small for cross-validation splits.
    if len(X_train) < 20:
        print("Dataset too small for cross-validation calibration. Using base XGBoost.")
        clf = MultiOutputClassifier(base_xgb)
    else:
        clf = MultiOutputClassifier(CalibratedClassifierCV(estimator=base_xgb, method='sigmoid', cv=3))
    
    clf.fit(X_train, Y_train)
    
    print("Evaluating Model Performance on Test Set...")
    prob_preds = clf.predict_proba(X_test)
    
    metrics_report = {}
    for i, target in enumerate(TARGETS):
        # Calibrated classifier returns a list of arrays (one per output)
        y_true = Y_test[:, i]
        y_prob = prob_preds[i][:, 1]
        y_pred = (y_prob >= 0.5).astype(int)
        
        auc = roc_score = 0.5
        if len(np.unique(y_true)) > 1:
            auc = roc_auc_score(y_true, y_prob)
            
        brier = brier_score_loss(y_true, y_prob)
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
        npv = tn / (tn + fn) if (tn + fn) > 0 else 0.0
        sens = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        
        metrics_report[target] = {
            "AUC": float(auc),
            "Brier_Score": float(brier),
            "Sensitivity": float(sens),
            "NPV": float(npv),
            "TP": int(tp), "FP": int(fp), "TN": int(tn), "FN": int(fn)
        }
        print(f"  {target.ljust(12)} | AUC: {auc:.3f} | NPV: {npv:.3f} | Sens: {sens:.3f}")

    return clf, metrics_report


def update_bayesian_priors(df):
    print("Recomputing Bayesian Outcome Tables...")
    priors = {}
    
    # Calculate global success rates per generation 
    # using smoothed empirical probability (Laplace smoothing)
    for target in TARGETS:
        success = int(df[target].sum())
        total = int(df[target].notnull().sum())
        # Add pseudo-counts to prevent 0 or 100% priors
        priors[target] = {
            "success": success + 1,
            "total": total + 2,
            "baseline_prob": round((success + 1) / (total + 2), 4)
        }
    return priors


def save_artifacts(clf, preprocessor, feature_names, metrics_report, priors, num_samples):
    print("Saving Artifacts to Disk...")
    
    # 1. Model Bundle (Includes preprocessor for inference)
    bundle = {
        "preprocessor": preprocessor,
        "model": clf,
        "feature_names": feature_names
    }
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(bundle, f)
        
    # 2. Thresholds (Dynamic calculation based on NPV constraints could go here, using defaults for safety)
    thresholds = {
        "green_min": 0.70,   # >= 70% susceptibility -> Green
        "amber_min": 0.40    # 40-69% -> Amber
    }
    with open(THRESHOLDS_PATH, "w") as f:
        json.dump(thresholds, f, indent=4)
        
    # 3. Features
    features_manifest = {
        "numerical": NUMERIC_FEATURES,
        "categorical": CATEGORICAL_FEATURES,
        "one_hot_columns": feature_names
    }
    with open(FEATURES_PATH, "w") as f:
        json.dump(features_manifest, f, indent=4)
        
    # 4. Bayesian Priors
    with open(EVIDENCE_PATH, "w") as f:
        json.dump(priors, f, indent=4)
        
    # 5. Metadata
    meta = {
        "version": "v2",
        "training_timestamp": datetime.now().isoformat(),
        "total_samples": num_samples,
        "dataset_fingerprint": str(num_samples) + " rows",
        "metrics": metrics_report
    }
    with open(META_PATH, "w") as f:
        json.dump(meta, f, indent=4)
        
    # 6. Audit Log (CSV append)
    log_df = pd.DataFrame([{
        "Date": datetime.now().isoformat(),
        "Version": "v2",
        "Samples": num_samples,
        "Gen1_NPV": metrics_report["Gen1"]["NPV"],
        "Carbapenem_AUC": metrics_report["Carbapenem"]["AUC"]
    }])
    if os.path.exists(AUDIT_LOG_CSV):
        log_df.to_csv(AUDIT_LOG_CSV, mode='a', header=False, index=False)
    else:
        log_df.to_csv(AUDIT_LOG_CSV, index=False)

    print("Artifacts successfully generated and saved.")


def run_pipeline():
    print("="*60)
    print(" BETA-LACTAM AUTOMATED RETRAINING PIPELINE TRIGGERED")
    print("="*60)
    
    try:
        engine = connect_db()
        backup_old_artifacts()
        
        df = load_data(engine)
        num_samples = len(df)
        
        X, Y, feature_names, preprocessor = preprocess_data(df)
        
        clf, metrics_report = train_model(X, Y, feature_names)
        
        priors = update_bayesian_priors(df)
        
        save_artifacts(clf, preprocessor, feature_names, metrics_report, priors, num_samples)
        
        print("\n✅ RETRAINING PIPELINE COMPLETED SUCCESSFULLY.")
        print(f"Backend containers must be restarted to load `v2` artifacts from `/api/config/`.")
        
    except Exception as e:
        print(f"\n❌ RETRAINING PIPELINE FAILED: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    run_pipeline()
