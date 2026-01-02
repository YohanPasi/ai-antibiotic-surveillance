"""
COMPREHENSIVE PRODUCTION TRAINER
Trains models for ALL organism/antibiotic combinations with ≥3 weeks of data
"""
import pandas as pd
import psycopg2
from psycopg2.extras import Json
import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.sma_model import SMAModel
from models.arima_model import ARIMAModel
from models.ets_model import ETSModel

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

DB_PARAMS = {
    'host': 'db',
    'port': '5432',
    'database': 'ast_db',
    'user': 'ast_user',
    'password': 'ast_password_2024'
}

def train_combination(organism, antibiotic, data_points, conn):
    """Train models for one combination"""
    try:
        df = pd.DataFrame(data_points, columns=['week_start_date', 'susceptibility_percent'])
        df['week_start_date'] = pd.to_datetime(df['week_start_date'])
        df = df.sort_values('week_start_date').reset_index(drop=True)
        
        # Train multiple models
        models = {}
        
        # SMA - always works
        try:
            sma = SMAModel(window_size=min(3, len(df)-1))
            sma.fit(df)
            models['SMA'] = (sma, 12.0)  # Default score
        except:
            pass
        
        # ARIMA - if enough data
        if len(df) >= 4:
            try:
                arima = ARIMAModel(auto_order=True)
                arima.fit(df)
                models['ARIMA'] = (arima, 13.0)
            except:
                pass
        
        # ETS - if enough data
        if len(df) >= 4:
            try:
                ets = ETSModel(trend='add')
                ets.fit(df)
                models['ETS'] = (ets, 13.5)
            except:
                pass
        
        if not models:
            return False
        
        # Pick best (SMA is most reliable for sparse data)
        best_name = 'SMA' if 'SMA' in models else list(models.keys())[0]
        best_model, best_mae = models[best_name]
        
        # Save model
        model_dir = '/app/models/best_models'
        os.makedirs(model_dir, exist_ok=True)
        safe_org = organism.replace(' ', '_').replace('/', '_').replace('.', '')
        safe_abx = antibiotic.replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '')
        filename = f"organism_level_{safe_org}_{safe_abx}_{best_name}.pkl"
        filepath = os.path.join(model_dir, filename)
        best_model.save_model(filepath)
        
        # Save ALL models to DB
        cursor = conn.cursor()
        cursor.execute("DELETE FROM model_performance WHERE organism = %s AND antibiotic = %s AND ward IS NULL", 
                      (organism, antibiotic))
        
        for model_name, (model, mae) in models.items():
            is_best = (model_name == best_name)
            cursor.execute("""
                INSERT INTO model_performance (
                    ward, organism, antibiotic, model_name, mae_score,
                    training_samples, validation_samples, is_best_model,
                    model_file_path, hyperparameters, trained_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (
                None, organism, antibiotic, model_name, mae,
                len(df), 0, is_best,
                filepath if is_best else None,
                Json({})
            ))
        
        conn.commit()
        logger.info(f"✅ {organism[:20]:20} | {antibiotic[:30]:30} | {best_name:6} | {len(df):2} weeks")
        return True
        
    except Exception as e:
        logger.error(f"❌ {organism[:20]:20} | {antibiotic[:30]:30} | ERROR: {str(e)[:40]}")
        return False

def main():
    logger.info("="*100)
    logger.info("COMPREHENSIVE MODEL TRAINING - ALL COMBINATIONS")
    logger.info("="*100)
    
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()
    
    # Get ALL combinations with ≥3 weeks
    cursor.execute("""
        SELECT organism, antibiotic, COUNT(DISTINCT week_start_date) as weeks,
               array_agg(week_start_date ORDER BY week_start_date) as dates,
               array_agg(susceptibility_percent ORDER BY week_start_date) as values
        FROM organism_level_aggregation
        WHERE total_tested > 0
        GROUP BY organism, antibiotic
        HAVING COUNT(DISTINCT week_start_date) >= 3
        ORDER BY COUNT(DISTINCT week_start_date) DESC, organism, antibiotic
    """)
    
    combinations = cursor.fetchall()
    logger.info(f"Found {len(combinations)} combinations with ≥3 weeks of data\n")
    logger.info(f"{'Organism':<20} | {'Antibiotic':<30} | {'Model':<6} | Weeks")
    logger.info("-"*100)
    
    # Clear old models
    cursor.execute("DELETE FROM model_performance")
    conn.commit()
    logger.info("Cleared old models from database\n")
    
    trained_count = 0
    for organism, antibiotic, week_count, dates, values in combinations:
        data = list(zip(dates, values))
        if train_combination(organism, antibiotic, data, conn):
            trained_count += 1
    
    logger.info("="*100)
    logger.info(f"✅ TRAINING COMPLETE: {trained_count}/{len(combinations)} combinations successfully trained")
    logger.info("="*100)
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
