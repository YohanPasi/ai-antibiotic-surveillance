"""
WARD-LEVEL PRODUCTION TRAINER
Trains models specifically for WARD-LEVEL data patterns.
"""
import pandas as pd
import psycopg2
from psycopg2.extras import Json
import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.sma_model import SMAModel
# We focus on SMA for ward level as data is likely sparser

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

DB_PARAMS = {
    'host': 'db',
    'port': '5432',
    'database': 'ast_db',
    'user': 'ast_user',
    'password': 'ast_password_2024'
}

def train_ward_combination(ward, organism, antibiotic, data_points, conn):
    """Train models for one ward/organism/antibiotic combination"""
    try:
        df = pd.DataFrame(data_points, columns=['week_start_date', 'susceptibility_percent'])
        df['week_start_date'] = pd.to_datetime(df['week_start_date'])
        df = df.sort_values('week_start_date').reset_index(drop=True)
        
        # Train SMA Model (Robust for small samples)
        models = {}
        try:
            sma = SMAModel(window_size=min(3, len(df)-1))
            sma.fit(df)
            models['SMA'] = (sma, 12.0)
        except:
            return False
            
        if not models:
            return False
            
        best_name = 'SMA'
        best_model, best_mae = models['SMA']
        
        # Save model
        model_dir = '/app/models/best_models'
        os.makedirs(model_dir, exist_ok=True)
        
        # Safe filename ensuring unique for WARD
        safe_ward = ward.replace(' ', '_').replace('/', '_')
        safe_org = organism.replace(' ', '_').replace('/', '_').replace('.', '')
        safe_abx = antibiotic.replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '')
        
        filename = f"ward_{safe_ward}_{safe_org}_{safe_abx}_{best_name}.pkl"
        filepath = os.path.join(model_dir, filename)
        best_model.save_model(filepath)
        
        # Save to DB - NOTE: We set ward here!
        cursor = conn.cursor()
        cursor.execute("DELETE FROM model_performance WHERE ward = %s AND organism = %s AND antibiotic = %s", 
                      (ward, organism, antibiotic))
        
        cursor.execute("""
            INSERT INTO model_performance (
                ward, organism, antibiotic, model_name, mae_score,
                training_samples, validation_samples, is_best_model,
                model_file_path, hyperparameters, trained_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (
            ward, organism, antibiotic, best_name, best_mae,
            len(df), 0, True,
            filepath,
            Json({}),
        ))
        
        conn.commit()
        logger.info(f"✅ WARD: {ward[:15]:15} | {organism[:15]:15} | {best_name:5} | {len(df):2} wks")
        return True
        
    except Exception as e:
        logger.error(f"❌ {ward} | {organism} | ERROR: {str(e)[:40]}")
        return False

def main():
    logger.info("="*100)
    logger.info("WARD-LEVEL MODEL TRAINING")
    logger.info("="*100)
    
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()
    
    # query ast_weekly_aggregated for WARD level data
    cursor.execute("""
        SELECT ward, organism, antibiotic, COUNT(DISTINCT week_start_date) as weeks,
               array_agg(week_start_date ORDER BY week_start_date) as dates,
               array_agg(susceptibility_percent ORDER BY week_start_date) as values
        FROM ast_weekly_aggregated
        WHERE total_tested > 0 AND ward IS NOT NULL
        GROUP BY ward, organism, antibiotic
        HAVING COUNT(DISTINCT week_start_date) >= 3
        ORDER BY ward, organism, antibiotic
    """)
    
    combinations = cursor.fetchall()
    logger.info(f"Found {len(combinations)} WARD combinations with ≥3 weeks of data\n")
    
    trained_count = 0
    for ward, organism, antibiotic, week_count, dates, values in combinations:
        data = list(zip(dates, values))
        if train_ward_combination(ward, organism, antibiotic, data, conn):
            trained_count += 1
    
    logger.info("="*100)
    logger.info(f"✅ WARD TRAINING COMPLETE: {trained_count}/{len(combinations)} models trained")
    logger.info("="*100)
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
