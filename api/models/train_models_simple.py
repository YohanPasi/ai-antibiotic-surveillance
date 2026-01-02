"""
Simplified Model Trainer - Robust Version
Trains SMA, ARIMA, ETS, and Ensemble models (skip Prophet due to compatibility issue)
"""
import numpy as np
import pandas as pd
import psycopg2
from psycopg2.extras import Json
import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import warnings

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.sma_model import SMAModel
from models.arima_model import ARIMAModel
from models.ets_model import ETSModel
from models.ensemble_model import EnsembleModel

warnings.filterwarnings('ignore')

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

def rolling_origin_cv(data: pd.DataFrame, min_train_size: int = 4, n_splits: int = 3) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
    """Create rolling-origin cross-validation splits."""
    splits = []
    total_points = len(data)
    
    if total_points < min_train_size + 1:
        logger.warning(f"Insufficient data for CV ({total_points} points). Using simple split.")
        train = data.iloc[:-1]
        test = data.iloc[-1:]
        return [(train, test)]
    
    max_splits = min(n_splits, total_points - min_train_size)
    
    for i in range(max_splits):
        train_end = min_train_size + i
        test_idx = train_end
        
        if test_idx >= total_points:
            break
        
        train = data.iloc[:train_end]
        test = data.iloc[test_idx:test_idx+1]
        splits.append((train, test))
    
    return splits

def train_model_combination(ward: str, organism: str, antibiotic: str, conn):
    """Train models for a specific combination."""
    logger.info(f"\n{'='*80}")
    logger.info(f"Ward={ward}, Organism={organism}, Antibiotic={antibiotic}")
    
    cursor = conn.cursor()
    
    if ward:
        query = """
            SELECT week_start_date, susceptibility_percent
            FROM ast_weekly_aggregated
            WHERE ward = %s AND organism = %s AND antibiotic = %s
              AND total_tested > 0
            ORDER BY week_start_date
        """
        cursor.execute(query, (ward, organism, antibiotic))
    else:
        query = """
            SELECT week_start_date, susceptibility_percent
            FROM organism_level_aggregation
            WHERE organism = %s AND antibiotic = %s
              AND total_tested > 0
            ORDER BY week_start_date
        """
        cursor.execute(query, (organism, antibiotic))
    
    rows = cursor.fetchall()
    cursor.close()
    
    if len(rows) < 4:
        logger.warning(f"Insufficient data ({len(rows)} points). Skipping.")
        return None
    
    data = pd.DataFrame(rows, columns=['week_start_date', 'susceptibility_percent'])
    data['week_start_date'] = pd.to_datetime(data['week_start_date'])
    data = data.sort_values('week_start_date').reset_index(drop=True)
    
    logger.info(f"Data points: {len(data)}")
    
    # Create CV splits
    cv_splits = rolling_origin_cv(data)
    
    # Test models
    models_to_test = {
        'SMA': SMAModel(window_size=4, use_exponential=True, alpha=0.3),
        'ARIMA': ARIMAModel(auto_order=True),
        'ETS': ETSModel(trend='add', damped_trend=True)
    }
    
    model_scores = {}
    trained_models = []
    
    for model_name, model in models_to_test.items():
        logger.info(f"Testing {model_name}...")
        mae_scores = []
        
        for train, test in cv_splits:
            try:
                model_copy = type(model)(**model.hyperparameters) if hasattr(model, 'hyperparameters') else type(model)()
                model_copy.fit(train)
                pred, _, _ = model_copy.predict(steps=1)
                actual = test['susceptibility_percent'].values[0]
                
                if not np.isnan(actual):
                    error = abs(pred - actual)
                    mae_scores.append(error)
            except Exception as e:
                logger.debug(f"  {model_name} CV failed: {str(e)}")
                continue
        
        if len(mae_scores) > 0:
            avg_mae = np.mean(mae_scores)
            # Re-fit on all data
            model.fit(data)
            model_scores[model_name] = {'mae': avg_mae, 'model': model}
            trained_models.append(model)
            logger.info(f"  {model_name} MAE: {avg_mae:.2f}%")
        else:
            logger.warning(f"  {model_name} failed all CV splits")
    
    # Create ensemble if multiple models succeeded
    if len(trained_models) >= 2:
        logger.info("Creating Ensemble...")
        mae_values = [model_scores[m.name]['mae'] for m in trained_models]
        inv_mae = [1.0 / (mae + 1e-6) for mae in mae_values]
        weights = [w / sum(inv_mae) for w in inv_mae]
        
        ensemble = EnsembleModel(trained_models.copy(), method='weighted', weights=weights)
        ensemble.fit(data)
        
        # Test ensemble
        ensemble_scores = []
        for train, test in cv_splits:
            try:
                temp_models = []
                for m in trained_models:
                    temp_m = type(m)(**m.hyperparameters) if hasattr(m, 'hyperparameters') else type(m)()
                    temp_m.fit(train)
                    temp_models.append(temp_m)
                
                temp_ensemble = EnsembleModel(temp_models, method='weighted', weights=weights)
                temp_ensemble.is_trained = True
                pred, _, _ = temp_ensemble.predict(steps=1)
                actual = test['susceptibility_percent'].values[0]
                
                if not np.isnan(actual):
                    ensemble_scores.append(abs(pred - actual))
            except:
                continue
        
        if len(ensemble_scores) > 0:
            avg_mae = np.mean(ensemble_scores)
            model_scores['Ensemble'] = {'mae': avg_mae, 'model': ensemble}
            logger.info(f"  Ensemble MAE: {avg_mae:.2f}%")
    
    if not model_scores:
        logger.error("All models failed")
        return None
    
    # Select best model
    best_name = min(model_scores, key=lambda k: model_scores[k]['mae'])
    best_model = model_scores[best_name]['model']
    logger.info(f"🏆 Best: {best_name} (MAE: {model_scores[best_name]['mae']:.2f}%)")
    
    # Save model
    model_dir = '/app/models/best_models'
    os.makedirs(model_dir, exist_ok=True)
    ward_str = ward if ward else 'organism_level'
    model_filename = f"{ward_str}_{organism}_{antibiotic}_{best_name}.pkl".replace(' ', '_').replace('/', '_')
    model_path = os.path.join(model_dir, model_filename)
    best_model.save_model(model_path)
    
    return {
        'best_model_name': best_name,
        'mae': model_scores[best_name]['mae'],
        'training_samples': len(data),
        'model_path': model_path,
        'all_scores': {name: scores['mae'] for name, scores in model_scores.items()}
    }

def main():
    logger.info("="*80)
    logger.info("STARTING ADVANCED MODEL TRAINING")
    logger.info("="*80)
    
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()
    
    # Get combinations with sufficient data
    query = """
        SELECT DISTINCT ward, organism, antibiotic
        FROM ast_weekly_aggregated
        WHERE total_tested > 0
        GROUP BY ward, organism, antibiotic
        HAVING COUNT(*) >= 4
    """
    cursor.execute(query)
    combinations = cursor.fetchall()
    
    # Organism-level
    query_org = """
        SELECT DISTINCT NULL, organism, antibiotic
        FROM organism_level_aggregation
        WHERE total_tested > 0
        GROUP BY organism, antibiotic
        HAVING COUNT(*) >= 4
    """
    cursor.execute(query_org)
    org_combinations = cursor.fetchall()
    
    all_combos = list(combinations) + list(org_combinations)
    logger.info(f"Found {len(all_combos)} combinations to train")
    
    # Clear existing records
    cursor.execute("DELETE FROM model_performance")
    conn.commit()
    
    trained_count = 0
    
    for ward, organism, antibiotic in all_combos:
        result = train_model_combination(ward, organism, antibiotic, conn)
        
        if result:
            for model_name, mae in result['all_scores'].items():
                is_best = (model_name == result['best_model_name'])
                
                insert_query = """
                    INSERT INTO model_performance (
                        ward, organism, antibiotic, model_name, mae_score,
                        training_samples, validation_samples, is_best_model,
                        model_file_path, hyperparameters
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                cursor.execute(insert_query, (
                    ward, organism, antibiotic, model_name, mae,
                    result['training_samples'], 0,
                    is_best,
                    result['model_path'] if is_best else None,
                    Json({})
                ))
            
            conn.commit()
            trained_count += 1
    
    logger.info("\n" + "="*80)
    logger.info(f"✓ Training Complete: {trained_count}/{len(all_combos)} combinations")
    logger.info("="*80)
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
