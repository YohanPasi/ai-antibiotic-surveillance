import pandas as pd
import joblib
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models import MRSAPrediction

# ============================
# PATHS
# ============================

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
DATA_WEEKLY = PROJECT_ROOT / "data" / "weekly"
MODELS_DIR = PROJECT_ROOT / "ml" / "mrsa"

LIGHT1_MODEL = MODELS_DIR / "mrsa_light1.pkl"
LIGHT4_MODEL = MODELS_DIR / "mrsa_light4.pkl"


# ==========================================
# REQUIRED FEATURE COLUMNS FOR BOTH MODELS
# ==========================================

LIGHT1_FEATURES = ["ward", "sample_type", "collection_time"]
LIGHT4_FEATURES = ["ward", "sample_type", "collection_time", "gram",
                   "cefoxitin_result", "oxacillin_result",
                   "vancomycin_result", "clindamycin_result", "erythromycin_result"]


# ==========================================
# LOAD MODELS
# ==========================================

def load_models():
    print("Loading MRSA models...")
    model_l1 = joblib.load(LIGHT1_MODEL)
    model_l4 = joblib.load(LIGHT4_MODEL)
    print("Models loaded successfully.")
    return model_l1, model_l4


# ==========================================
# CLEAN WEEKLY INPUT
# ==========================================

def preprocess_weekly(df: pd.DataFrame):
    df = df.rename(columns=lambda c: c.strip().lower().replace(" ", "_"))
    
    # Convert timestamp column if needed
    if "collection_time" in df.columns:
        df["collection_time"] = pd.to_datetime(df["collection_time"], errors="coerce")

    return df


# ==========================================
# RUN PREDICTION + SAVE TO DB
# ==========================================

def run_prediction_and_save(df, model, model_type, db: Session):
    feature_cols = LIGHT1_FEATURES if model_type == "light1" else LIGHT4_FEATURES

    # Missing columns → fill with default values
    for col in feature_cols:
        if col not in df.columns:
            df[col] = None

    X = df[feature_cols]

    preds = model.predict_proba(X)[:, 1]  # probability of MRSA (label 1)
    labels = (preds >= 0.5).astype(int)

    saved_count = 0

    for i in range(len(df)):
        entry = MRSAPrediction(
            sample_id=str(df.loc[i, "sample_id"]),
            ward=df.loc[i, "ward"],
            sample_type=df.loc[i, "sample_type"],
            organism=df.loc[i].get("organism"),
            gram=df.loc[i].get("gram"),
            model_type=model_type,
            probability=float(preds[i]),
            predicted_label=int(labels[i]),
            created_at=datetime.utcnow()
        )
        db.add(entry)
        saved_count += 1

    db.commit()
    return saved_count


# ==========================================
# MAIN PIPELINE EXECUTION
# ==========================================

def main():
    print("\n=== MRSA WEEKLY PIPELINE STARTED ===")

    # Load latest file
    files = sorted(DATA_WEEKLY.glob("*.csv"))
    if not files:
        print("No weekly files found in data/weekly/")
        return

    latest_file = files[-1]
    print(f"Using weekly file: {latest_file}")

    df = pd.read_csv(latest_file)
    df = preprocess_weekly(df)

    # Load ML models
    model_l1, model_l4 = load_models()

    # Database session
    db = SessionLocal()

    # Run predictions for Light-1
    print("\nRunning Light-1 predictions...")
    count_l1 = run_prediction_and_save(df, model_l1, "light1", db)
    print(f"Light-1 predictions saved: {count_l1}")

    # Run predictions for Light-4
    print("\nRunning Light-4 predictions...")
    count_l4 = run_prediction_and_save(df, model_l4, "light4", db)
    print(f"Light-4 predictions saved: {count_l4}")

    print("\n=== MRSA WEEKLY PIPELINE COMPLETED SUCCESSFULLY ===")


if __name__ == "__main__":
    main()
