"""
Model Trainer with Rolling-Origin Cross-Validation
Trains multiple models, evaluates using time-series CV, and selects best model
Implements ensemble methods for maximum accuracy
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
from models.prophet_model import ProphetModel
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

class ModelTrainer:
    """
    Orchestrates model training with rolling-origin cross-validation.
    Supports multiple models and automatic best-model selection.
    """
    
    def __init__(self, min_train_size: int = 4, n_splits: int = 3):
        """
        Initialize model trainer.
        
        Args:
            min_train_size: Minimum number of weeks for training (default: 4)
            n_splits: Number of cross-validation splits (default: 3)
        """
        self.min_train_size = min_train_size
        self.n_splits = n_splits
        self.models = {}
        self.results = {}
        
    def _rolling_origin_cv(self, data: pd.DataFrame) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
        """
        Create rolling-origin cross-validation splits.
        
        Train on weeks 1 to N, predict week N+1
        Train on weeks 1 to N+1, predict week N+2
        etc.
        
        Args:
            data: Time series data sorted by date
            
        Returns:
            List of (train, test) DataFrame tuples
        """
        splits = []
        total_points = len(data)
        
        if total_points < self.min_train_size + 1:
            logger.warning(f"Insufficient data for CV ({total_points} points). Using simple train/test split.")
            # Simple split: use last point as test
            train = data.iloc[:-1]
            test = data.iloc[-1:]
            return [(train, test)]
        
        # Calculate split points
        max_splits = min(self.n_splits, total_points - self.min_train_size)
        
        for i in range(max_splits):
            train_end = self.min_train_size + i
            test_idx = train_end
            
            if test_idx >= total_points:
                break
            
            train = data.iloc[:train_end]
            test = data.iloc[test_idx:test_idx+1]
            
            splits.append((train, test))
        
        logger.info(f"Created {len(splits)} rolling-origin CV splits")
        return splits
    
    def _train_and_evaluate_model(self, model, train_data: pd.DataFrame, test_data: pd.DataFrame) -> Dict:
        """
        Train a single model and evaluate on test data.
        
        Args:
            model: Model instance (SMA, Prophet, or ARIMA)
            train_data: Training data
            test_data: Test data (single row)
            
        Returns:
            Dictionary with evaluation metrics
        """
        try:
            # Fit model
            model.fit(train_data)
            
            # Predict
            pred, lower, upper = model.predict(steps=1)
            
            # Get actual value
            actual = test_data['susceptibility_percent'].values[0]
            
            # Calculate error
            if not np.isnan(actual):
                error = abs(pred - actual)
                return {
                    'mae': error,
                    'prediction': pred,
                    'actual': actual,
                    'lower_bound': lower,
                    'upper_bound': upper,
                    'success': True
                }
            else:
                return {'success': False}
                
        except Exception as e:
            logger.warning(f"Model {model.name} failed: {str(e)}")
            return {'success': False}
    
    def train_models_for_combination(self, 
                                     ward: str, 
                                     organism: str, 
                                     antibiotic: str,
                                     conn) -> Dict:
        """
        Train all models for a specific ward/organism/antibiotic combination.
        
        Args:
            ward: Ward name (or None for organism-level)
            organism: Organism name
            antibiotic: Antibiotic name
            conn: Database connection
            
        Returns:
            Dictionary with best model and performance metrics
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"Training models for: Ward={ward}, Organism={organism}, Antibiotic={antibiotic}")
        logger.info(f"{'='*80}")
        
        # Fetch historical data
        cursor = conn.cursor()
        
        if ward:
            query = """
                SELECT week_start_date, susceptibility_percent, total_tested
                FROM ast_weekly_aggregated
                WHERE ward = %s AND organism = %s AND antibiotic = %s
                  AND total_tested > 0
                ORDER BY week_start_date
            """
            cursor.execute(query, (ward, organism, antibiotic))
        else:
            # Organism-level (aggregate across wards)
            query = """
                SELECT week_start_date, susceptibility_percent, total_tested
                FROM organism_level_aggregation
                WHERE organism = %s AND antibiotic = %s
                  AND total_tested > 0
                ORDER BY week_start_date
            """
            cursor.execute(query, (organism, antibiotic))
        
        rows = cursor.fetchall()
        cursor.close()
        
        if len(rows) < self.min_train_size:
            logger.warning(f"Insufficient data ({len(rows)} points). Skipping combination.")
            return None
        
        # Create DataFrame
        data = pd.DataFrame(rows, columns=['week_start_date', 'susceptibility_percent', 'total_tested'])
        data['week_start_date'] = pd.to_datetime(data['week_start_date'])
        data = data.sort_values('week_start_date').reset_index(drop=True)
        
        logger.info(f"Loaded {len(data)} weeks of historical data")
        
        # Create CV splits
        cv_splits = self._rolling_origin_cv(data)
        
        # Initialize models with optimized parameters
        models_to_test = {
            'SMA': SMAModel(window_size=4, use_exponential=True, alpha=0.3),
            'Prophet': ProphetModel(changepoint_prior_scale=0.05, seasonality_prior_scale=0.1),
            'ARIMA': ARIMAModel(auto_order=True),
            'ETS': ETSModel(trend='add', damped_trend=True)
        }
        
        # Train and evaluate each model
        model_scores = {}
        trained_models = []
        
        for model_name, model in models_to_test.items():
            logger.info(f"\nTesting {model_name} model...")
            mae_scores = []
            
            for train, test in cv_splits:
                result = self._train_and_evaluate_model(model, train, test)
                
                if result['success']:
                    mae_scores.append(result['mae'])
            
            if len(mae_scores) > 0:
                avg_mae = np.mean(mae_scores)
                model_scores[model_name] = {
                    'mae': avg_mae,
                    'cv_scores': mae_scores,
                    'model': model
                }
                trained_models.append(model)
                logger.info(f"  {model_name} - Average MAE: {avg_mae:.2f}%")
            else:
                logger.warning(f"  {model_name} - Failed on all CV splits")
        
        # CREATE ENSEMBLE MODEL if we have multiple successful models
        if len(trained_models) >= 2:
            logger.info(f"\nCreating Ensemble model from {len(trained_models)} base models...")
            
            # Calculate inverse-MAE weights (better models get higher weight)
            mae_values = [model_scores[m.name]['mae'] for m in trained_models]
            inv_mae = [1.0 / (mae + 1e-6) for mae in mae_values]  # Add small epsilon to avoid division by zero
            weights = [w / sum(inv_mae) for w in inv_mae]  # Normalize
            
            # Create weighted ensemble
            ensemble = EnsembleModel(
                base_models=trained_models.copy(),
                method='weighted',
                weights=weights
            )
            
            # "Fit" ensemble (just stores the weights)
            ensemble.fit(data)
            
            # Test ensemble
            ensemble_scores = []
            for train, test in cv_splits:
                # Re-fit base models on this split
                temp_models = []
                for model_name, model in models_to_test.items():
                    try:
                        temp_model = type(model)(**model.hyperparameters) if hasattr(model, 'hyperparameters') else type(model)()
                        temp_model.fit(train)
                        temp_models.append(temp_model)
                    except:
                        continue
                
                if len(temp_models) >= 2:
                    temp_ensemble = EnsembleModel(temp_models, method='weighted', weights=weights)
                    temp_ensemble.is_trained = True
                    result = self._train_and_evaluate_model(temp_ensemble, train, test)
                    if result['success']:
                        ensemble_scores.append(result['mae'])
            
            if len(ensemble_scores) > 0:
                avg_mae = np.mean(ensemble_scores)
                model_scores['Ensemble'] = {
                    'mae': avg_mae,
                    'cv_scores': ensemble_scores,
                    'model': ensemble
                }
                logger.info(f"  Ensemble - Average MAE: {avg_mae:.2f}% (weights: {[f'{w:.2f}' for w in weights]})")
        
        # Select best model
        if not model_scores:
            logger.error("No models succeeded. Cannot select best model.")
            return None
        
        best_model_name = min(model_scores, key=lambda k: model_scores[k]['mae'])
        best_score = model_scores[best_model_name]
        
        logger.info(f"\n🏆 Best Model: {best_model_name} (MAE: {best_score['mae']:.2f}%)")
        
        # Re-train best model on all data
        best_model = best_score['model']
        best_model.fit(data)
        
        # Save model
        model_dir = '/app/models/best_models'
        os.makedirs(model_dir, exist_ok=True)
        
        ward_str = ward if ward else 'organism_level'
        model_filename = f"{ward_str}_{organism}_{antibiotic}_{best_model_name}.pkl".replace(' ', '_').replace('/', '_')
        model_path = os.path.join(model_dir, model_filename)
        
        best_model.save_model(model_path)
        logger.info(f"✓ Model saved to: {model_path}")
        
        # Return results
        return {
            'best_model_name': best_model_name,
            'mae': best_score['mae'],
            'training_samples': len(data),
            'validation_samples': len(cv_splits),
            'model_path': model_path,
            'all_scores': {name: scores['mae'] for name, scores in model_scores.items()}
        }
    
    def train_all_combinations(self):
        """
        Train models for all valid ward/organism/antibiotic combinations.
        """
        logger.info("="*80)
        logger.info("STARTING MODEL TRAINING FOR ALL COMBINATIONS")
        logger.info("="*80)
        
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
        
        # Get all unique combinations with sufficient data
        query = """
            SELECT DISTINCT ward, organism, antibiotic, COUNT(*) as data_points
            FROM ast_weekly_aggregated
            WHERE total_tested > 0
            GROUP BY ward, organism, antibiotic
            HAVING COUNT(*) >= %s
        """
        cursor.execute(query, (self.min_train_size,))
        combinations = cursor.fetchall()
        
        logger.info(f"Found {len(combinations)} combinations with sufficient data (>={self.min_train_size} points)")
        
        # Also get organism-level combinations
        query_org = """
            SELECT DISTINCT NULL as ward, organism, antibiotic, COUNT(*) as data_points
            FROM organism_level_aggregation
            WHERE total_tested > 0
            GROUP BY organism, antibiotic
            HAVING COUNT(*) >= %s
        """
        cursor.execute(query_org, (self.min_train_size,))
        org_combinations = cursor.fetchall()
        
        logger.info(f"Found {len(org_combinations)} organism-level combinations")
        
        # Combine
        all_combinations = list(combinations) + list(org_combinations)
        
        # Train models for each combination
        trained_count = 0
        failed_count = 0
        
        # Clear existing model performance records
        cursor.execute("DELETE FROM model_performance")
        conn.commit()
        
        for ward, organism, antibiotic, data_points in all_combinations:
            result = self.train_models_for_combination(ward, organism, antibiotic, conn)
            
            if result:
                # Store in database
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
                        result['training_samples'], result['validation_samples'],
                        is_best,
                        result['model_path'] if is_best else None,
                        Json({})  # Hyperparameters can be added later
                    ))
                
                conn.commit()
                trained_count += 1
            else:
                failed_count += 1
        
        logger.info("\n" + "="*80)
        logger.info("MODEL TRAINING COMPLETE")
        logger.info("="*80)
        logger.info(f"Successfully trained: {trained_count} combinations")
        logger.info(f"Failed: {failed_count} combinations")
        logger.info("="*80)
        
        cursor.close()
        conn.close()

if __name__ == "__main__":
    trainer = ModelTrainer(min_train_size=4, n_splits=3)
    trainer.train_all_combinations()
