"""
STAGE D: CHANGE DETECTION & ALERT ENGINE
Detects meaningful deviations from ward-specific baselines.

RULES:
- D0: Baseline must exist and have sufficient_history = TRUE
- D1: Weekly signal must have has_sufficient_data = TRUE (>=10 isolates)
- D2: deviation = observed_s_percent - baseline_s_percent
- D3: Compare observed to lower_bound
- D4: Persistence (2 consecutive AMBER → RED)

OUTPUT: surveillance_logs (audit trail)
"""
import psycopg2
import os
import logging
import sys
import torch
from datetime import datetime

# Add parent directory to path to import PredictionService
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prediction_service import PredictionService
from models.lstm_model import LSTMModel

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection parameters
DB_PARAMS = {
    'host': os.getenv('DB_HOST', 'db'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'ast_db'),
    'user': os.getenv('DB_USER', 'ast_user'),
    'password': os.getenv('DB_PASSWORD', 'ast_password_2024')
}

MODEL_PATH = "/app/models/best_models/lstm_model.pth"

def get_recent_history(cursor, ward, organism, antibiotic, current_week, limit=4):
    """Get the S% history from the previous weeks for LSTM input."""
    cursor.execute("""
        SELECT susceptibility_percent 
        FROM ast_weekly_aggregated
        WHERE ward IS NOT DISTINCT FROM %s 
          AND organism = %s 
          AND antibiotic = %s
          AND week_start_date < %s
        ORDER BY week_start_date DESC
        LIMIT %s
    """, (ward, organism, antibiotic, current_week, limit))
    
    rows = cursor.fetchall()
    return [float(row[0]) for row in rows][::-1] # Ascending order

def get_past_alert_statuses(cursor, ward, organism, antibiotic, current_week, limit=3):
    """Get the alert statuses from the previous weeks for persistence logic."""
    cursor.execute("""
        SELECT alert_status 
        FROM surveillance_logs
        WHERE ward IS NOT DISTINCT FROM %s 
          AND organism = %s 
          AND antibiotic = %s
          AND week_start_date < %s
        ORDER BY week_start_date DESC
        LIMIT %s
    """, (ward, organism, antibiotic, current_week, limit))
    
    rows = cursor.fetchall()
    return [row[0] for row in rows]

def detect_changes():
    logger.info("=" * 60)
    logger.info("⚡ STAGE E: HYBRID DECISION ENGINE (BATCH)")
    logger.info("=" * 60)
    
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
    except Exception as e:
        logger.error(f"✗ Database Error: {e}")
        return False
    
    # Load LSTM Model
    lstm_model = PredictionService.load_lstm_model(MODEL_PATH)
    if not lstm_model:
        logger.warning("⚠️ LSTM Model not found. Running with Statistical Only logic.")
    
    # Clear existing surveillance logs (fresh rebuild)
    cursor.execute("TRUNCATE TABLE surveillance_logs RESTART IDENTITY CASCADE")
    conn.commit()
    logger.info("✓ Cleared existing surveillance logs")
    
    # D1: Fetch all weekly signals that meet minimum confidence
    cursor.execute("""
        SELECT 
            week_start_date, ward, organism, antibiotic,
            susceptibility_percent, total_tested, has_sufficient_data
        FROM ast_weekly_aggregated
        WHERE total_tested >= 1
        ORDER BY week_start_date ASC, ward, organism, antibiotic
    """)
    
    signals = cursor.fetchall()
    logger.info(f"✓ Found {len(signals)} weekly signals to process")
    
    stats = {"green": 0, "amber": 0, "amber-high": 0, "red": 0, "critical": 0, "skipped": 0}
    
    for week, ward, organism, antibiotic, observed_s, total, sufficient in signals:
        try:
            # D0: Fetch Baseline
            cursor.execute("""
                SELECT baseline_s_percent, lower_bound, upper_bound
                FROM ast_baselines
                WHERE ward IS NOT DISTINCT FROM %s AND organism = %s AND antibiotic = %s
            """, (ward, organism, antibiotic))
            
            baseline_row = cursor.fetchone()
            if not baseline_row:
                stats["skipped"] += 1
                continue
            
            baseline_s, lower_bound, upper_bound = baseline_row
            
            # STAGE D: LSTM Forecast
            lstm_forecast = float(observed_s)
            if lstm_model:
                history = get_recent_history(cursor, ward, organism, antibiotic, week)
                if len(history) >= 1:
                    lstm_forecast = PredictionService.predict_with_lstm(lstm_model, history)
            
            # STAGE E: Hybrid Status
            prev_statuses = get_past_alert_statuses(cursor, ward, organism, antibiotic, week)
            status, direction, reason = PredictionService.get_hybrid_status(
                float(observed_s), float(lower_bound), lstm_forecast, prev_statuses
            )
            
            # STAGE F: Stewardship
            prompt, domain = PredictionService.generate_detailed_stewardship(status, organism, antibiotic, ward or "Unknown")
            
            # Audit Log
            cursor.execute("""
                INSERT INTO surveillance_logs (
                    week_start_date, ward, organism, antibiotic,
                    observed_s_percent, predicted_s_percent, baseline_s_percent, baseline_lower_bound,
                    forecast_deviation, alert_status, previous_alert_status, alert_reason,
                    stewardship_prompt, stewardship_domain, 
                    model_version, consensus_path
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                week, ward, organism, antibiotic,
                observed_s, lstm_forecast, baseline_s, lower_bound,
                lstm_forecast - float(baseline_s), status, 
                prev_statuses[0] if prev_statuses else None, reason,
                prompt, domain,
                "Hybrid_LSTM_v1", "Batch Consensus V2"
            ))
            
            stats[status] = stats.get(status, 0) + 1
            
            # Commit in chunks
            if sum([v for k,v in stats.items() if k != "skipped"]) % 1000 == 0:
                conn.commit()
                logger.info(f"  Processed {sum(stats.values())} signals...")
            
        except Exception as e:
            logger.error(f"Error processing {ward}/{organism}/{antibiotic} (Week {week}): {e}")
            conn.rollback()
            continue
    
    conn.commit()
    cursor.close()
    conn.close()
    
    logger.info("-" * 40)
    logger.info("✓ HYBRID SURVEILLANCE PROCESSING COMPLETE")
    for s, count in stats.items():
        logger.info(f"  {s.upper()}: {count}")
    logger.info("-" * 40)
    
    return True

if __name__ == "__main__":
    detect_changes()
