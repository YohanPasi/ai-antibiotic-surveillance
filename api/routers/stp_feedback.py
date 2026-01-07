
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from pydantic import BaseModel, Field
from database import get_db
import hashlib
from datetime import datetime

# Enforce M50: Surveillance Only Disclaimer
DISCLAIMER_TEXT = "SURVEILLANCE ONLY. NOT FOR CLINICAL DIAGNOSIS. (M50)"

router = APIRouter(
    prefix="/api/stp/feedback",
    tags=["STP Feedback Loop"],
    responses={
        200: {"description": "Success"},
        400: {"description": "Invalid Request"},
        429: {"description": "Rate Limit Exceeded"}
    }
)

# ===== PYDANTIC MODELS =====

class ASTResult(BaseModel):
    antibiotic: str
    result: str = Field(..., pattern="^(S|I|R|NA)$")

class AntibiogramSubmission(BaseModel):
    ward: str
    organism: str
    sample_date: str  # ISO date
    data_source: str = Field(..., pattern="^(LIS|MANUAL)$")
    isolates: List[List[ASTResult]]

class ValidationResponse(BaseModel):
    ward: str
    organism: str
    antibiotic: str
    predicted_rate: float
    observed_rate: float
    absolute_error: float
    within_ci: bool
    completeness_ratio: float
    status: str

class ModelStatus(BaseModel):
    model_id: str
    type: str
    status: str
    validations: int
    pass_rate: float
    avg_error:float

# ===== HELPER FUNCTIONS =====

def generate_fingerprint(ward: str, organism: str, sample_date: str, 
                        isolate_num: int, antibiotic: str, result: str) -> str:
    """Generate unique fingerprint for duplicate detection."""
    fingerprint_input = f"{ward}|{organism}|{sample_date}|{isolate_num}|{antibiotic}|{result}"
    return hashlib.sha256(fingerprint_input.encode()).hexdigest()

def get_active_model(db: Session) -> str:
    """Retrieve currently active model ID for version locking."""
    active_model = db.execute(text("""
        SELECT model_id FROM stp_model_registry 
        WHERE status = 'active' 
        ORDER BY created_at DESC 
        LIMIT 1
    """)).scalar()
    return str(active_model) if active_model else None

# ===== ENDPOINTS =====

@router.post("/antibiogram")
def submit_antibiogram(
    submission: AntibiogramSubmission,
    db: Session = Depends(get_db)
):
    """
    Submit raw isolate-level AST results with duplicate protection (FIX #1).
    Model version locked at submission time (FIX #4).
    """
    
    # FIX #4: Capture active model version
    active_model = get_active_model(db)
    if not active_model:
        raise HTTPException(status_code=500, detail="No active model found")
    
    inserted_count = 0
    duplicate_count = 0
    errors = []
    
    for isolate_idx, isolate in enumerate(submission.isolates):
        for ast in isolate:
            # FIX #1: Generate fingerprint
            fingerprint = generate_fingerprint(
                submission.ward,
                submission.organism,
                submission.sample_date,
                isolate_idx,
                ast.antibiotic,
                ast.result
            )
            
            try:
                db.execute(text("""
                    INSERT INTO stp_external_ast_raw 
                    (ward, organism, antibiotic, ast_result, sample_date, 
                     isolate_number, submission_fingerprint, data_source, model_id, submitted_by)
                    VALUES (:ward, :organism, :antibiotic, :result, :date, 
                            :isolate_num, :fingerprint, :source, :model_id, :user_id)
                """), {
                    "ward": submission.ward,
                    "organism": submission.organism,
                    "antibiotic": ast.antibiotic,
                    "result": ast.result,
                    "date": submission.sample_date,
                    "isolate_num": isolate_idx,
                    "fingerprint": fingerprint,
                    "source": submission.data_source,
                    "model_id": active_model,
                    "user_id": None  # From auth context in production
                })
                db.flush()  # Trigger constraint check
                inserted_count += 1
            except IntegrityError as e:
                # Duplicate fingerprint or constraint violation
                error_str = str(e)
                if 'submission_fingerprint' in error_str or 'unique' in error_str.lower():
                    duplicate_count += 1
                else:
                    errors.append(f"{ast.antibiotic}: {error_str[:100]}")
                db.rollback()
            except Exception as e:
                errors.append(f"{ast.antibiotic}: {str(e)[:100]}")
                db.rollback()
    
    if inserted_count > 0:
        try:
            db.commit()
            
            # CRITICAL: Trigger derivation and validation
            from services.stp_derive_rates import derive_resistance_rates
            try:
                derive_resistance_rates(
                    ward=submission.ward,
                    organism=submission.organism,
                    sample_date=submission.sample_date,
                    db=db
                )
            except Exception as e:
                # Log but don't fail submission if derivation fails
                errors.append(f"Derivation error: {str(e)[:100]}")
                
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Commit failed: {str(e)}")
    
    return {
        "message": "Antibiogram submitted successfully",
        "inserted": inserted_count,
        "duplicates_rejected": duplicate_count,
        "errors": errors if errors else None,
        "disclaimer": DISCLAIMER_TEXT
    }

@router.get("/validation")
def get_validation_results(
    ward: Optional[str] = None,
    min_completeness: float = 0.7,
    db: Session = Depends(get_db)
):
    """
    Compare predicted vs observed outcomes (FIX #3: Quality filtered).
    Returns only validations meeting completeness threshold.
    """
    query = """
    SELECT 
        v.ward,
        v.organism,
        v.antibiotic,
        v.predicted_rate,
        v.observed_rate,
        v.absolute_error,
        v.within_ci,
        v.completeness_ratio,
        CASE 
            WHEN v.within_ci THEN 'PASS'
            ELSE 'MISS'
        END as status
    FROM stp_prediction_validation_events v
    WHERE (:ward IS NULL OR v.ward = :ward)
      AND v.completeness_ratio >= :min_completeness
    ORDER BY v.validated_at DESC
    LIMIT 50
    """
    
    results = db.execute(text(query), {
        "ward": ward,
        "min_completeness": min_completeness
    }).fetchall()
    
    return {
        "validations": [
            {
                "ward": r.ward,
                "organism": r.organism,
                "antibiotic": r.antibiotic,
                "predicted_rate": round(r.predicted_rate, 3),
                "observed_rate": round(r.observed_rate, 3),
                "absolute_error": round(r.absolute_error, 3),
                "within_ci": r.within_ci,
                "completeness_ratio": round(r.completeness_ratio, 2),
                "status": r.status
            } for r in results
        ],
        "disclaimer": DISCLAIMER_TEXT
    }

@router.get("/model-status")
def get_model_feedback_status(db: Session = Depends(get_db)):
    """
    Model performance summary for transparency (M61, M70).
    Shows validation metrics and drift signals.
    """
    query = """
    SELECT 
        m.model_id,
        m.model_type,
        m.status,
        COUNT(v.validation_id) as total_validations,
        SUM(CASE WHEN v.within_ci THEN 1 ELSE 0 END) as passed_validations,
        AVG(v.absolute_error) as avg_error
    FROM stp_model_registry m
    LEFT JOIN stp_prediction_validation_events v ON m.model_id = v.model_id
    WHERE m.status != 'archived'
    GROUP BY m.model_id, m.model_type, m.status
    """
    
    results = db.execute(text(query)).fetchall()
    
    return {
        "models": [
            {
                "model_id": str(r.model_id),
                "type": r.model_type,
                "status": r.status,
                "validations": r.total_validations or 0,
                "pass_rate": round((r.passed_validations or 0) / max(r.total_validations or 1, 1), 2),
                "avg_error": round(r.avg_error or 0, 3)
            } for r in results
        ],
        "disclaimer": DISCLAIMER_TEXT
    }

@router.post("/trigger-retraining")
def trigger_retraining(
    model_id: str,
    reason: str,
    db: Session = Depends(get_db)
):
    """
    Request model retraining (FIX #5: Rate limited to 30 days).
    Human approval required (M61, M67).
    """
    
    # FIX #5: Check cooldown period
    recent_trigger = db.execute(text("""
        SELECT event_id FROM stp_model_lifecycle_events
        WHERE model_id = :model_id
          AND event_type = 'RETRAINING_TRIGGERED'
          AND created_at > NOW() - INTERVAL '30 days'
    """), {"model_id": model_id}).scalar()
    
    if recent_trigger:
        raise HTTPException(
            status_code=429,
            detail="Retraining cooldown active (30 days). Last trigger within window."
        )
    
    # Log event (M62, M66)
    db.execute(text("""
        INSERT INTO stp_model_lifecycle_events (model_id, event_type, trigger_reason)
        VALUES (:model_id, 'RETRAINING_TRIGGERED', :reason)
    """), {"model_id": model_id, "reason": reason})
    db.commit()
    
    return {
        "message": "Retraining request logged. Awaiting human approval.",
        "disclaimer": DISCLAIMER_TEXT
    }


# =====================================================
# OUTBREAK VS DRIFT DISCRIMINATOR ENDPOINTS
# =====================================================

@router.get("/outbreak-alerts")
def get_outbreak_alerts(
    status: str = "new",
    confirmed_only: bool = False,
    db: Session = Depends(get_db)
):
    """
    Get ward-level outbreak alerts (separate from model drift).
    REFINEMENT #4: Only 'confirmed' outbreaks shown if confirmed_only=True.
    """
    
    if confirmed_only:
        status = "confirmed"
    
    query = text("""
    SELECT 
        outbreak_id, ward, organism, antibiotic, detected_week,
        validation_count, avg_deviation, severity, status,
        source_model_id, detected_at
    FROM stp_outbreak_events
    WHERE (:status = 'all' OR status = :status)
    ORDER BY severity DESC, detected_at DESC
    LIMIT 50
    """)
    
    results = db.execute(query, {"status": status}).fetchall()
    
    return {
        "outbreaks": [
            {
                "id": str(r.outbreak_id),
                "ward": r.ward,
                "organism": r.organism,
                "antibiotic": r.antibiotic,
                "week": r.detected_week.isoformat(),
                "evidence_count": r.validation_count,
                "avg_deviation": round(r.avg_deviation * 100, 1),
                "severity": r.severity,
                "status": r.status,
                "model_id": str(r.source_model_id) if r.source_model_id else None
            } for r in results
        ],
        "disclaimer": "Epidemiological surveillance only. Clinical correlation required. (M50)"
    }


@router.post("/outbreak-alerts/{outbreak_id}/confirm")
def confirm_outbreak(
    outbreak_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    REFINEMENT #4: Human confirmation gate.
    Only confirmed outbreaks escalate to clinical dashboards.
    """
    
    db.execute(text("""
        UPDATE stp_outbreak_events
        SET status = 'confirmed',
            reviewed_by = :user_id,
            reviewed_at = NOW()
        WHERE outbreak_id = :outbreak_id
    """), {"outbreak_id": outbreak_id, "user_id": user_id})
    db.commit()
    
    return {"message": "Outbreak confirmed. Now visible on clinical dashboards."}


@router.get("/drift-analysis")
def get_drift_analysis(
    lookback_days: int = 14,
    db: Session = Depends(get_db)
):
    """
    Analyze systemic drift (≥3 wards affected).
    REFINEMENT #2: EXCLUDES outbreak-linked validation events.
    """
    
    query = text("""
    SELECT 
        organism, antibiotic,
        COUNT(DISTINCT ward) as affected_wards,
        AVG(absolute_error) as avg_error,
        COUNT(*) as total_violations
    FROM stp_prediction_validation_events
    WHERE within_ci = FALSE
      AND validated_at > NOW() - CAST(:lookback_days || ' days' AS INTERVAL)
      AND linked_outbreak_id IS NULL  -- CRITICAL: Exclude outbreak data
    GROUP BY organism, antibiotic
    HAVING COUNT(DISTINCT ward) >= 3
       AND AVG(absolute_error) > 0.10
    ORDER BY avg_error DESC
    """)
    
    results = db.execute(query, {"lookback_days": lookback_days}).fetchall()
    
    return {
        "drift_signals": [
            {
                "organism": r.organism,
                "antibiotic": r.antibiotic,
                "affected_wards": r.affected_wards,
                "avg_error": round(r.avg_error, 3),
                "retraining_recommended": r.avg_error > 0.15,
                "note": "Multi-ward pattern suggests model drift, not outbreak"
            } for r in results
        ],
        "safeguard": "Outbreak-linked validations excluded from drift calculation",
        "disclaimer": DISCLAIMER_TEXT
    }
