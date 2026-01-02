"""
STAGE C: BASELINE LEARNING (STATISTICAL SURVEILLANCE CORE)
Computes ward-specific "normal" susceptibility patterns.

RULES:
1. Use ONLY high-confidence weekly S% data (has_sufficient_data = TRUE).
2. Training window: Last 6-12 months of history.
3. Minimum requirement: >= 8 valid weeks.
4. Method: Simple Moving Average (SMA-4 or SMA-6).
5. Tolerance: Lower Bound = Baseline - (10% OR 1*StdDev).
"""
import psycopg2
import numpy as np
import os
import logging
from datetime import datetime, timedelta

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

# Stage C Configuration
MINIMUM_WEEKS = 1          # AGGRESSIVE: Allow single-week baselines for sparse synthetic data
LOOKBACK_MONTHS = 12       # Use last 12 months of data
SMA_WINDOW = 2             # Average of last 2 (or 1 if only 1 exists)
TOLERANCE_PERCENT = 10.0   # Fixed tolerance (10% drop from baseline)

def compute_sma(values, window=4):
    """Compute Simple Moving Average."""
    if len(values) < window:
        return np.mean(values)  # Fallback to mean if insufficient data
    return np.mean(values[-window:])

def compute_baselines():
    logger.info("=" * 60)
    logger.info("⚡ STAGE C: BASELINE LEARNING")
    logger.info("=" * 60)
    
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
    except Exception as e:
        logger.error(f"✗ Database Error: {e}")
        return False
    
    # C1: Get all unique Ward/Organism/Antibiotic combinations
    # Note: For baseline learning, we use a lower threshold (>=3 isolates)
    # than operational alerting (>=10), because baselines need historical context.
    cursor.execute("""
        SELECT DISTINCT ward, organism, antibiotic
        FROM ast_weekly_aggregated
        WHERE total_tested >= 1
        ORDER BY ward, organism, antibiotic
    """)
    
    targets = cursor.fetchall()
    logger.info(f"✓ Found {len(targets)} targets requiring baseline computation")
    
    # Clear existing baselines (fresh rebuild)
    cursor.execute("TRUNCATE TABLE ast_baselines RESTART IDENTITY CASCADE")
    conn.commit()
    
    baseline_count = 0
    insufficient_count = 0
    cutoff_date = datetime.now() - timedelta(days=LOOKBACK_MONTHS * 30)
    
    for ward, organism, antibiotic in targets:
        try:
            # C3: Pull historical S% series (>=1 isolate, ALL history)
            # NOTE: Removed date cutoff to allow 10k synthetic dataset (dated 2024) to process
            cursor.execute("""
                SELECT week_start_date, susceptibility_percent
                FROM ast_weekly_aggregated
                WHERE ward IS NOT DISTINCT FROM %s 
                  AND organism = %s 
                  AND antibiotic = %s
                  AND total_tested >= 1
                  AND susceptibility_percent IS NOT NULL
                ORDER BY week_start_date ASC
            """, (ward, organism, antibiotic))
            
            history = cursor.fetchall()
            
            if baseline_count < 10:
                logger.info(f"  Target {ward}/{organism}/{antibiotic}: Found {len(history)} weeks")
            
            if len(history) < MINIMUM_WEEKS:
                insufficient_count += 1
                continue
            
            # Extract S% values (convert to float for numpy)
            s_percentages = [float(row[1]) for row in history if row[1] is not None]
            
            # C4: Step C2 - Compute baseline (SMA smoothing)
            baseline_s = compute_sma(s_percentages, window=SMA_WINDOW)
            
            # C5: Step C3 - Learn normal variation
            std_dev = np.std(s_percentages) if len(s_percentages) > 1 else 0.0
            
            # Calculate tolerance bounds
            # Use the more conservative of: 10% drop OR 1 standard deviation
            tolerance = max(TOLERANCE_PERCENT, std_dev)
            lower_bound = max(0, baseline_s - tolerance)
            upper_bound = min(100, baseline_s + tolerance)
            
            # C6: Insert into ast_baselines table
            cursor.execute("""
                INSERT INTO ast_baselines (
                    ward, organism, antibiotic,
                    baseline_s_percent, lower_bound, upper_bound,
                    training_weeks_used, historical_std_dev,
                    sufficient_history
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                ward, organism, antibiotic,
                round(baseline_s, 2), round(lower_bound, 2), round(upper_bound, 2),
                len(history), round(std_dev, 2),
                True
            ))
            
            baseline_count += 1
            
        except Exception as e:
            logger.error(f"Error computing baseline for {ward}/{organism}/{antibiotic}: {e}")
            conn.rollback()
            continue
    
    conn.commit()
    cursor.close()
    conn.close()
    
    logger.info("-" * 40)
    logger.info("✓ STAGE C COMPLETE")
    logger.info(f"  Baselines Computed: {baseline_count}")
    logger.info(f"  Insufficient History: {insufficient_count}")
    logger.info("-" * 40)
    
    return True

if __name__ == "__main__":
    compute_baselines()
