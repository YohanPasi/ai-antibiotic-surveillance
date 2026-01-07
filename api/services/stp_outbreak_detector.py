from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, List

# =====================================================
# CRITICAL SAFEGUARD: "Outbreak ≠ Drift"
# =====================================================
# Outbreak-classified deviations MUST NOT contribute to drift statistics.
# This is enforced by:
# 1. Linking validation events to outbreak_id
# 2. Filtering linked_outbreak_id IS NULL in drift calculations
# 3. Human confirmation gate before clinical escalation

def analyze_validation_failures(db: Session, lookback_days: int = 14) -> Dict:
    """
    REFINEMENT #5: Post-Deployment Discrimination Between Epidemiological Events and Model Drift.
    
    Classify validation failures as:
    - Ward-level outbreak (local deviation)
    - Systemic drift (model failure)
    - Isolated noise
    """
    
    # Step 1: Detect Ward-Level Outbreaks
    ward_outbreaks = detect_ward_outbreaks(db, lookback_days)
    
    # Step 2: REFINEMENT #2 - Detect Systemic Drift (EXCLUDING outbreak data)
    systemic_drift = detect_model_drift(db, lookback_days)
    
    return {
        "ward_outbreaks": ward_outbreaks,
        "drift_signals": systemic_drift
    }


def detect_ward_outbreaks(db: Session, lookback_days: int) -> List[Dict]:
    """
    Detect ward-level outbreaks using conservative rules:
    - ≥2 CI violations in same ward/organism/antibiotic
    - Other wards must be stable (localized deviation)
    - REFINEMENT #1: Track source model for audit trail
    """
    
    query = text("""
    WITH ward_failures AS (
        SELECT 
            ward, organism, antibiotic,
            COUNT(*) as violation_count,
            AVG(absolute_error) as avg_deviation,
            DATE_TRUNC('week', validated_at) as week,
            mode() WITHIN GROUP (ORDER BY model_id) as source_model_id,
            array_agg(validation_id) as validation_ids
        FROM stp_prediction_validation_events
        WHERE within_ci = FALSE
          AND validated_at > NOW() - CAST(:lookback_days || ' days' AS INTERVAL)
          AND linked_outbreak_id IS NULL  -- Only unlinked events
        GROUP BY ward, organism, antibiotic, DATE_TRUNC('week', validated_at)
        HAVING COUNT(*) >= 2
    ),
    other_wards_stable AS (
        SELECT 
            wf.organism, wf.antibiotic, wf.week,
            COUNT(DISTINCT v.ward) as other_ward_count
        FROM ward_failures wf
        JOIN stp_prediction_validation_events v
            ON wf.organism = v.organism
            AND wf.antibiotic = v.antibiotic
            AND wf.week = DATE_TRUNC('week', v.validated_at)
            AND wf.ward != v.ward
            AND v.within_ci = TRUE
            AND v.validated_at > NOW() - CAST(:lookback_days || ' days' AS INTERVAL)
        GROUP BY wf.organism, wf.antibiotic, wf.week
    )
    SELECT 
        wf.ward, wf.organism, wf.antibiotic, wf.week,
        wf.violation_count, wf.avg_deviation, wf.source_model_id,
        wf.validation_ids,
        CASE 
            WHEN wf.avg_deviation > 0.25 THEN 'HIGH'
            WHEN wf.avg_deviation > 0.15 THEN 'MEDIUM'
            ELSE 'LOW'
        END as severity
    FROM ward_failures wf
    LEFT JOIN other_wards_stable ows
        ON wf.organism = ows.organism
        AND wf.antibiotic = ows.antibiotic
        AND wf.week = ows.week
    WHERE COALESCE(ows.other_ward_count, 0) >= 1  -- At least 1 other ward stable
    """)
    
    results = db.execute(query, {"lookback_days": lookback_days}).fetchall()
    
    outbreaks = []
    for r in results:
        # REFINEMENT #3: Alert Fatigue Control via UNIQUE constraint
        # REFINEMENT #4: Default status = 'new' (requires review before escalation)
        outbreak_result = db.execute(text("""
            INSERT INTO stp_outbreak_events 
            (ward, organism, antibiotic, detected_week, validation_count, 
             avg_deviation, severity, status, source_model_id)
            VALUES (:ward, :organism, :antibiotic, :week, :count, 
                    :deviation, :severity, 'new', :model_id)
            ON CONFLICT (ward, organism, antibiotic, detected_week) 
            DO UPDATE SET 
                validation_count = EXCLUDED.validation_count,
                avg_deviation = EXCLUDED.avg_deviation,
                severity = EXCLUDED.severity,
                detected_at = NOW()
            RETURNING outbreak_id
        """), {
            "ward": r.ward,
            "organism": r.organism,
            "antibiotic": r.antibiotic,
            "week": r.week,
            "count": r.violation_count,
            "deviation": float(r.avg_deviation),
            "severity": r.severity,
            "model_id": r.source_model_id
        })
        
        outbreak_id = outbreak_result.scalar()
        
        # Link validation events to outbreak (REFINEMENT #2)
        for val_id in r.validation_ids:
            db.execute(text("""
                UPDATE stp_prediction_validation_events
                SET linked_outbreak_id = :outbreak_id
                WHERE validation_id = :val_id
            """), {"outbreak_id": outbreak_id, "val_id": val_id})
        
        outbreaks.append({
            "outbreak_id": str(outbreak_id),
            "ward": r.ward,
            "organism": r.organism,
            "antibiotic": r.antibiotic,
            "severity": r.severity,
            "evidence_count": r.violation_count
        })
    
    db.commit()
    return outbreaks


def detect_model_drift(db: Session, lookback_days: int) -> List[Dict]:
    """
    Detect systemic model drift (≥3 wards affected).
    
    REFINEMENT #2 (CRITICAL): EXCLUDES validation events linked to outbreaks.
    This prevents outbreak data from biasing retraining decisions.
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
      AND linked_outbreak_id IS NULL  -- EXCLUDE outbreak data
    GROUP BY organism, antibiotic
    HAVING COUNT(DISTINCT ward) >= 3
       AND AVG(absolute_error) > 0.10
    ORDER BY avg_error DESC
    """)
    
    results = db.execute(query, {"lookback_days": lookback_days}).fetchall()
    
    drift_signals = []
    for r in results:
        drift_signals.append({
            "organism": r.organism,
            "antibiotic": r.antibiotic,
            "affected_wards": r.affected_wards,
            "avg_error": round(float(r.avg_error), 3),
            "retraining_recommended": float(r.avg_error) > 0.15
        })
    
    return drift_signals


def get_escalatable_outbreaks(db: Session) -> List[Dict]:
    """
    REFINEMENT #4: Only return CONFIRMED outbreaks for clinical escalation.
    Prevents panic from unreviewed detections.
    """
    
    query = text("""
    SELECT 
        outbreak_id, ward, organism, antibiotic, detected_week,
        validation_count, avg_deviation, severity, 
        reviewed_by, reviewed_at
    FROM stp_outbreak_events
    WHERE status = 'confirmed'
    ORDER BY severity DESC, detected_week DESC
    LIMIT 50
    """)
    
    results = db.execute(query).fetchall()
    
    return [
        {
            "id": str(r.outbreak_id),
            "ward": r.ward,
            "organism": r.organism,
            "antibiotic": r.antibiotic,
            "week": r.detected_week.isoformat(),
            "evidence_count": r.validation_count,
            "avg_deviation": round(float(r.avg_deviation) * 100, 1),
            "severity": r.severity,
            "reviewed_by": str(r.reviewed_by) if r.reviewed_by else None,
            "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None
        } for r in results
    ]
