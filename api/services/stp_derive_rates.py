
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime

# Expected antibiotic panels per organism (FIX #3: Completeness reference)
EXPECTED_ANTIBIOTIC_PANELS = {
    "Escherichia coli": 10,
    "Klebsiella pneumoniae": 10,
    "Pseudomonas aeruginosa": 9,
    "Staphylococcus aureus": 8,
    "Enterococcus faecalis": 7,
    "Enterococcus faecium": 7,
    "Acinetobacter baumannii": 9,
    "default": 10  # Fallback
}

def derive_resistance_rates(ward: str, organism: str, sample_date: str, db: Session):
    """
    Derive resistance rates from raw AST submissions with completeness checking.
    Uses exact Stage 2 aggregation logic (M21, M22,M12 compliant).
    """
    
    # Get week start (align with STP pipeline)
    week_start_query = """
    SELECT DATE_TRUNC('week', :sample_date::date) as week_start
    """
    week_start = db.execute(text(week_start_query), {"sample_date": sample_date}).scalar()
    
    # Get expected antibiotic count for this organism
    expected_count = EXPECTED_ANTIBIOTIC_PANELS.get(organism, EXPECTED_ANTIBIOTIC_PANELS["default"])
    
    # Aggregate raw AST results with completeness calculation
    aggregation_query = """
    WITH counts AS (
        SELECT 
            ward,
            organism,
            antibiotic,
            SUM(CASE WHEN ast_result = 'S' THEN 1 ELSE 0 END) as s_count,
            SUM(CASE WHEN ast_result = 'I' THEN 1 ELSE 0 END) as i_count,
            SUM(CASE WHEN ast_result = 'R' THEN 1 ELSE 0 END) as r_count,
            SUM(CASE WHEN ast_result = 'NA' THEN 1 ELSE 0 END) as na_count
        FROM stp_external_ast_raw
        WHERE ward = :ward
          AND organism = :organism
          AND DATE_TRUNC('week', sample_date) = :week_start
        GROUP BY ward, organism, antibiotic
    ),
    tested_antibiotics AS (
        SELECT COUNT(DISTINCT antibiotic) as tested_ab_count
        FROM stp_external_ast_raw
        WHERE ward = :ward
          AND organism = :organism
          AND DATE_TRUNC('week', sample_date) = :week_start
    )
    INSERT INTO stp_external_resistance_derived (
        ward, organism, antibiotic, week_start,
        s_count, i_count, r_count, na_count, tested_count,
        resistance_rate, is_stable,
        completeness_ratio, expected_antibiotics, tested_antibiotics
    )
    SELECT 
        c.ward,
        c.organism,
        c.antibiotic,
        :week_start,
        c.s_count,
        c.i_count,
        c.r_count,
        c.na_count,
        (c.s_count + c.i_count + c.r_count) as tested_count,
        CASE 
            WHEN (c.s_count + c.i_count + c.r_count) = 0 THEN NULL
            ELSE c.r_count::float / (c.s_count + c.i_count + c.r_count)
        END as resistance_rate,
        (c.s_count + c.i_count + c.r_count) >= 10 as is_stable,
        ta.tested_ab_count::float / :expected_count as completeness_ratio,
        :expected_count,
        ta.tested_ab_count
    FROM counts c
    CROSS JOIN tested_antibiotics ta
    ON CONFLICT (ward, organism, antibiotic, week_start) 
    DO UPDATE SET
        s_count = EXCLUDED.s_count,
        i_count = EXCLUDED.i_count,
        r_count = EXCLUDED.r_count,
        na_count = EXCLUDED.na_count,
        tested_count = EXCLUDED.tested_count,
        resistance_rate = EXCLUDED.resistance_rate,
        is_stable = EXCLUDED.is_stable,
        completeness_ratio = EXCLUDED.completeness_ratio,
        tested_antibiotics = EXCLUDED.tested_antibiotics,
        derived_at = NOW()
    """
    
    db.execute(text(aggregation_query), {
        "ward": ward,
        "organism": organism,
        "week_start": week_start,
        "expected_count": expected_count
    })
    db.commit()
    
    # Trigger validation with model version locking (FIX #4)
    trigger_validation(ward, organism, week_start, db)


def trigger_validation(ward: str, organism: str, week_start: str, db: Session):
    """
    Compare observed rates with predictions using submission-time model (FIX #4: Model version locked).
    Only validates antibiograms meeting quality thresholds.
    """
    
    validation_query = """
    INSERT INTO stp_prediction_validation_events (
        model_id, ward, organism, antibiotic,
        predicted_rate, observed_rate, lower_ci, upper_ci,
        absolute_error, within_ci, completeness_ratio
    )
    SELECT 
        raw.model_id,
        d.ward,
        d.organism,
        d.antibiotic,
        p.predicted_probability as predicted_rate,
        d.resistance_rate as observed_rate,
        p.lower_ci,
        p.upper_ci,
        ABS(d.resistance_rate - p.predicted_probability) as absolute_error,
        (d.resistance_rate BETWEEN COALESCE(p.lower_ci, 0) AND COALESCE(p.upper_ci, 1)) as within_ci,
        d.completeness_ratio
    FROM stp_external_resistance_derived d
    JOIN (
        SELECT DISTINCT ward, organism, model_id 
        FROM stp_external_ast_raw 
        WHERE ward = :ward
          AND organism = :organism
          AND DATE_TRUNC('week', sample_date) = :week_start
        LIMIT 1
    ) raw ON d.ward = raw.ward AND d.organism = raw.organism
    JOIN stp_model_predictions p 
        ON d.ward = p.ward 
        AND d.organism = p.organism 
        AND d.antibiotic = p.antibiotic
        AND DATE_TRUNC('week', p.forecast_week) = :week_start
        AND p.model_id = raw.model_id
    WHERE d.ward = :ward
      AND d.organism = :organism
      AND d.week_start = :week_start
      AND d.is_stable = TRUE
      AND d.completeness_ratio >= 0.7
      AND d.resistance_rate IS NOT NULL
    ON CONFLICT DO NOTHING
    """
    
    try:
        db.execute(text(validation_query), {
            "ward": ward,
            "organism": organism,
            "week_start": week_start
        })
        db.commit()
    except Exception as e:
        print(f"Validation trigger failed for {ward}/{organism}: {e}")
        db.rollback()


def check_retraining_eligibility(model_id: str, db: Session) -> dict:
    """
    Analyze validation results to determine if retraining is warranted.
    Returns trigger signals based on drift/performance metrics.
    """
    
    metrics_query = """
    SELECT 
        COUNT(*) as total_validations,
        SUM(CASE WHEN within_ci THEN 1 ELSE 0 END) as passed,
        AVG(absolute_error) as avg_error,
        STDDEV(absolute_error) as std_error
    FROM stp_prediction_validation_events
    WHERE model_id = :model_id
      AND validated_at > NOW() - INTERVAL '30 days'
    """
    
    result = db.execute(text(metrics_query), {"model_id": model_id}).fetchone()
    
    if not result or result.total_validations == 0:
        return {"eligible": False, "reason": "Insufficient validation data"}
    
    pass_rate = result.passed / result.total_validations
    
    # Trigger conditions
    triggers = []
    if pass_rate < 0.7:
        triggers.append("CI pass rate below 70%")
    if result.avg_error > 0.15:
        triggers.append("Average error exceeds 15%")
    if result.std_error and result.std_error > 0.2:
        triggers.append("High error variance (drift signal)")
    
    return {
        "eligible": len(triggers) > 0,
        "triggers": triggers,
        "metrics": {
            "validations": result.total_validations,
            "pass_rate": round(pass_rate, 2),
            "avg_error": round(result.avg_error, 3)
        }
    }
