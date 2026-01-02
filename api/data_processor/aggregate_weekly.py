"""
STAGE B: AGGREGATION & SIGNAL CONSTRUCTION
Converts raw isolate data into weekly surveillance signals.

RULES:
1. S=1 (Susceptible), I=0 (Intermediate), R=0 (Resistant).
2. Time Bucket: ISO Week (Monday start).
3. Grouping: Week + Ward + Organism + Antibiotic.
4. Calculation: S% = (Count S / Total) * 100.
5. Signal Confidence: Mark 'Low Confidence' if Total < 3.
"""
import psycopg2
import os
import logging
from datetime import timedelta

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

def get_iso_week_start(date):
    """Get the Monday of the ISO week."""
    return date - timedelta(days=date.weekday())

def aggregate_weekly_data():
    logger.info("=" * 60)
    logger.info("⚡ STAGE B: SIGNAL CONSTRUCTION")
    logger.info("=" * 60)
    
    # Connect
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
    except Exception as e:
        logger.error(f"✗ Database Error: {e}")
        return False
        
    # Clear Aggregation Table (Fresh Build)
    cursor.execute("TRUNCATE TABLE ast_weekly_aggregated RESTART IDENTITY CASCADE")
    conn.commit()
    
    # 1. FETCH RAW DATA (BULK)
    # Only fetching what passed Stage A (Non-Fermenters)
    cursor.execute("""
        SELECT date, ward, sub_organism, antibiotic_results
        FROM ast_raw_data
        WHERE date IS NOT NULL 
          AND ward IS NOT NULL 
          AND sub_organism IS NOT NULL
        ORDER BY date ASC
    """)
    raw_records = cursor.fetchall()
    logger.info(f"✓ Input: {len(raw_records)} isolate records from Bulk Data")

    # 1b. FETCH MANUAL ENTRIES
    cursor.execute("""
        SELECT entry_date, ward, organism, antibiotic, result
        FROM ast_manual_entry
        WHERE entry_date IS NOT NULL
    """)
    manual_records = cursor.fetchall()
    logger.info(f"✓ Input: {len(manual_records)} isolate records from Manual Entry")
    
    # 2. AGGREGATE IN MEMORY
    # Key: (WeekStart, Ward, Organism, Antibiotic)
    # Value: {S: count, I: count, R: count}
    signals = {}
    
    for date, ward, organism, ab_results in raw_records:
        if not ab_results: continue
        
        # B2: Time Bucketing -> ISO Week
        week_start = get_iso_week_start(date)
        
        for antibiotic, sir in ab_results.items():
            if not sir: continue
            
            key = (week_start, ward, organism, antibiotic)
            
            if key not in signals:
                signals[key] = {'S': 0, 'I': 0, 'R': 0, 'Total': 0}
            
            # B1: Convert AST to Signal
            signals[key]['Total'] += 1
            if sir == 'S':
                signals[key]['S'] += 1
            elif sir == 'I':
                signals[key]['I'] += 1 
            elif sir == 'R':
                signals[key]['R'] += 1

    # 2b. PROCESS MANUAL ENTRIES
    for date, ward, organism, antibiotic, result in manual_records:
        if not result: continue
        
        # Normalize Result
        res = result.upper()
        
        # B2: Time Bucketing
        week_start = get_iso_week_start(date)
        
        key = (week_start, ward, organism, antibiotic)
        
        if key not in signals:
            signals[key] = {'S': 0, 'I': 0, 'R': 0, 'Total': 0}
            
        signals[key]['Total'] += 1
        if res == 'S':
            signals[key]['S'] += 1
        elif res == 'I':
            signals[key]['I'] += 1
        elif res == 'R':
            signals[key]['R'] += 1
                
    # 3. COMPUTE S% & INSERT
    logger.info(f"✓ Generated {len(signals)} unique surveillance signals")
    
    insert_query = """
        INSERT INTO ast_weekly_aggregated (
            week_start_date, ward, organism, antibiotic,
            susceptible_count, intermediate_count, resistant_count
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    
    inserted = 0
    low_confidence = 0
    
    for (week, ward, org, abx), stats in signals.items():
        s_count = stats['S']
        i_count = stats['I']
        r_count = stats['R']
        
        # Track confidence for logging (even if DB handles the column)
        total = s_count + i_count + r_count
        if total < 3:
            low_confidence += 1
            
        cursor.execute(insert_query, (
            week, ward, org, abx, 
            s_count, i_count, r_count
        ))
        inserted += 1
        
    conn.commit()
    cursor.close()
    conn.close()
    
    logger.info("-" * 40)
    logger.info("✓ STAGE B COMPLETE")
    logger.info(f"  Total Signals: {inserted}")
    logger.info(f"  High Confidence (>=3 isolates): {inserted - low_confidence}")
    logger.info(f"  Low Confidence (<3 isolates):   {low_confidence}")
    logger.info("-" * 40)
    
    return True

if __name__ == "__main__":
    aggregate_weekly_data()
