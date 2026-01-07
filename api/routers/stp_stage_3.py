
"""
STP Stage 3: API Router
-----------------------
Read-only endpoints for Predictive Intelligence.
ENFORCES M25: Horizon Transparency.
ENFORCES M30: Non-Clinical Disclaimer.
ENFORCES M37: Human-in-Loop Status access.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from database import get_db
from sqlalchemy import text

router = APIRouter(
    prefix="/api/stp/stage3",
    tags=["STP Stage 3: Predictive Modeling"],
    responses={
        200: {"description": "Success"},
        400: {"description": "Invalid Request"}
    }
)

DISCLAIMER_TEXT = (
    "WARNING (M30): These predictions are for epidemiological surveillance and IPC planning only. "
    "NOT FOR CLINICAL DIAGNOSIS OR INDIVIDUAL PATIENT TREATMENT."
)

@router.get("/predictions", response_model=dict)
def get_predictions(
    ward: Optional[str] = None,
    organism: Optional[str] = None,
    horizon_weeks: int = Query(..., description="Forecast horizon in weeks (1-4)"),
    db: Session = Depends(get_db)
):
    """
    Get probabilistic resistance forecasts. (M25 Horizon enforced).
    """
    
    # Query stp_model_predictions JOIN stp_model_registry
    # Filter by horizon
    
    query = """
    SELECT 
        p.ward, p.organism, p.antibiotic, p.forecast_week, 
        p.predicted_probability, p.risk_level, 
        p.lower_ci, p.upper_ci,
        r.target, r.horizon, r.model_type
    FROM stp_model_predictions p
    JOIN stp_model_registry r ON p.model_id = r.model_id
    WHERE r.horizon = :horizon
    AND r.status = 'active'
    """
    
    params = {"horizon": horizon_weeks}
    
    if ward:
        query += " AND p.ward = :ward"
        params["ward"] = ward
    if organism:
        query += " AND p.organism = :organism"
        params["organism"] = organism
        
    query += " ORDER BY p.forecast_week DESC LIMIT 100"
    
    result = db.execute(text(query), params).fetchall()
    
    data = []
    for row in result:
        data.append({
            "ward": row.ward,
            "organism": row.organism,
            "antibiotic": row.antibiotic,
            "forecast_week": str(row.forecast_week),
            "probability": row.predicted_probability,
            "risk_level": row.risk_level,
            "uncertainty_interval": [row.lower_ci, row.upper_ci],
            "model_horizon": f"T+{row.horizon} Weeks"
        })
        
    return {
        "disclaimer": DISCLAIMER_TEXT, # M30
        "count": len(data),
        "data": data
    }

@router.get("/early-warnings", response_model=dict)
def get_early_warnings(
    status: Optional[str] = Query('new', description="Filter by status (new, reviewed)"),
    db: Session = Depends(get_db)
):
    """
    Get active early warning signals. Support M37 Review workflow.
    """
    query = """
    SELECT 
        warning_id, ward, organism, antibiotic, detected_at_week, 
        signal_strength, method, severity, status
    FROM stp_early_warnings
    WHERE status = :status
    ORDER BY detected_at_week DESC, signal_strength DESC
    """
    
    result = db.execute(text(query), {"status": status}).fetchall()
    
    data = []
    for row in result:
        data.append({
            "id": str(row.warning_id),
            "location": f"{row.ward} - {row.organism} - {row.antibiotic}",
            "week": str(row.detected_at_week),
            "strength": row.signal_strength,
            "severity": row.severity,
            "method": row.method,
            "status": row.status
        })
        
    return {
        "disclaimer": DISCLAIMER_TEXT,
        "data": data
    }

@router.get("/early-warning-cards", response_model=dict)
def get_early_warning_cards(
    db: Session = Depends(get_db)
):
    """
    Get formatted early warning cards for the dashboard.
    """
    query = """
    SELECT 
        warning_id, ward, organism, antibiotic, detected_at_week, 
        signal_strength, method, severity
    FROM stp_early_warnings
    WHERE status = 'new'
    ORDER BY signal_strength DESC
    LIMIT 10
    """
    
    result = db.execute(text(query)).fetchall()
    
    cards = []
    for row in result:
        # Map DB columns to Frontend 'prediction' object
        # probability = signal_strength (clamped 0-1)
        prob = row.signal_strength if row.signal_strength else 0.5
        prob = max(0, min(1, prob)) # Clamp
        
        cards.append({
            "ward": row.ward,
            "organism": row.organism,
            "antibiotic": row.antibiotic,
            "prediction": {
                "probability": round(prob, 2),
                "risk": (row.severity or "medium").lower(),
                "uncertainty": 0.1, # Placeholder or derive
                "horizon": "T+1"
            },
            "features": [
                {"name": "Signal Strength", "value": round(prob, 2)},
                {"name": "Detection Method", "value": 1.0 if row.method == 'TrendSlope' else 0.5},
            ]
        })
        
    return {
        "disclaimer": DISCLAIMER_TEXT,
        "count": len(cards),
        "data": cards
    }

@router.get("/explanations", response_model=dict)
def get_explanations(
    prediction_id: str,
    db: Session = Depends(get_db)
):
    """
    Get SHAP explanations for a prediction (M27).
    """
    query = """
    SELECT feature_name, importance_value, rank
    FROM stp_model_explanations
    WHERE prediction_id = :pid
    ORDER BY rank ASC
    LIMIT 10
    """
    
    # Check if prediction_id is UUID
    import uuid
    try:
        uuid_obj = uuid.UUID(prediction_id)
        result = db.execute(text(query), {"pid": prediction_id}).fetchall()
        top_features = [
            {"feature": row.feature_name, "impact": row.importance_value}
            for row in result
        ]
    except ValueError:
        # If not UUID, return empty (graceful degradation)
        top_features = []
    
    return {
        "disclaimer": DISCLAIMER_TEXT,
        "prediction_id": prediction_id,
        "top_features": top_features
    }
