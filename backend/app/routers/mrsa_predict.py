from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.base import SessionLocal
from app.db.models_mrsa import MrsaPrediction
import joblib
from datetime import datetime
import numpy as np
from pathlib import Path

router = APIRouter(prefix="/mrsa", tags=["MRSA Prediction"])

# Get the project root directory (two levels up from this file)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
MODEL_DIR = PROJECT_ROOT / "ml" / "mrsa"

# Load trained models
LIGHT1_MODEL = joblib.load(MODEL_DIR / "mrsa_light1.pkl")
LIGHT4_MODEL = joblib.load(MODEL_DIR / "mrsa_light4.pkl")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============  EARLY-STAGE PREDICTION (Light-1)  ================
@router.post("/predict/light1")
def predict_mrsa_light1(payload: dict, db: Session = Depends(get_db)):

    # Extract fields from user input
    sample = [
        payload.get("collection_time", 0),
        payload.get("ward", ""),
        payload.get("sample_type", ""),
        payload.get("organism", "")
    ]

    # Encode categorical (same as training)
    sample_arr = np.array(sample, dtype=object).reshape(1, -1)

    proba = float(LIGHT1_MODEL.predict_proba(sample_arr)[0][1])
    label = 1 if proba >= 0.5 else 0

    # Save to DB
    pred = MrsaPrediction(
        sample_id=payload.get("sample_id"),
        ward=payload.get("ward"),
        sample_type=payload.get("sample_type"),
        organism=payload.get("organism"),
        gram=None,  # Light-1 does not use gram
        model_type="light1",
        model_name="light1_model",
        probability=proba,
        predicted_label=label,
        p_mrsa=proba,
        created_at=datetime.utcnow()
    )
    
    db.add(pred)
    db.commit()
    db.refresh(pred)

    return {
        "status": "success",
        "model": "light1",
        "probability": proba,
        "predicted_label": label,
        "record_id": pred.id
    }



# ============  ADVANCED PREDICTION (Light-4)  ================
@router.post("/predict/light4")
def predict_mrsa_light4(payload: dict, db: Session = Depends(get_db)):

    sample = [
        payload.get("collection_time", 0),
        payload.get("ward", ""),
        payload.get("sample_type", ""),
        payload.get("organism", ""),
        payload.get("gram", "")
    ]

    sample_arr = np.array(sample, dtype=object).reshape(1, -1)

    proba = float(LIGHT4_MODEL.predict_proba(sample_arr)[0][1])
    label = 1 if proba >= 0.5 else 0

    pred = MrsaPrediction(
        sample_id=payload.get("sample_id"),
        ward=payload.get("ward"),
        sample_type=payload.get("sample_type"),
        organism=payload.get("organism"),
        gram=payload.get("gram"),
        model_type="light4",
        model_name="light4_model",
        probability=proba,
        predicted_label=label,
        p_mrsa=proba,
        created_at=datetime.utcnow()
    )

    db.add(pred)
    db.commit()

    return {
        "status": "success",
        "model": "light4",
        "probability": proba,
        "predicted_label": label
    }
