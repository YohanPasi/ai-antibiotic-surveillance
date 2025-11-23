from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.base import SessionLocal
from app.db.models import MRSAPrediction
import joblib
from datetime import datetime
import numpy as np

router = APIRouter(prefix="/mrsa", tags=["MRSA Prediction"])

# Load trained models
LIGHT1_MODEL = joblib.load("ml/mrsa/light1_model.pkl")
LIGHT4_MODEL = joblib.load("ml/mrsa/light4_model.pkl")

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
    pred = MRSAPrediction(
        sample_id=payload.get("sample_id"),
        ward=payload.get("ward"),
        sample_type=payload.get("sample_type"),
        organism=payload.get("organism"),
        gram=None,  # Light-1 does not use gram
        model_type="light1",
        probability=proba,
        predicted_label=label,
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

    pred = MRSAPrediction(
        sample_id=payload.get("sample_id"),
        ward=payload.get("ward"),
        sample_type=payload.get("sample_type"),
        organism=payload.get("organism"),
        gram=payload.get("gram"),
        model_type="light4",
        probability=proba,
        predicted_label=label,
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
