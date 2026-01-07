
"""
STP Stage 4: Evaluation Execution Script
----------------------------------------
Runs the full evaluation pipeline for a given model and dataset.
Connects to DB, runs BacktestEngine, and persists results.
"""

import sys
import os
import argparse
import logging
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Path setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from api.database import DATABASE_URL
    from api.evaluation_engine.stp_temporal_backtest import BacktestEngine
except ImportError:
    # Fallback
    from database import DATABASE_URL
    from api.evaluation_engine.stp_temporal_backtest import BacktestEngine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_evaluation(model_id: str, dataset_version: str):
    logger.info(f"🚀 Starting Evaluation for Model {model_id} on Dataset {dataset_version}")
    
    # Setup DB
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 1. Fetch Model Metadata (Mocked)
        # model = session.query(ModelRegistry).filter_by(model_id=model_id).first()
        model_metadata = {"model_id": model_id, "filepath": "mock.pkl"}
        
        # 2. Load Data (Mocked)
        logger.info("Loading Test Data (M41/M42)...")
        # Real logic: Load from stp_stage2_feature_store where version=dataset_version and is_frozen=True
        
        test_features = pd.DataFrame({
            'ward': ['Ward A', 'Ward B'] * 50,
            'organism': ['E. coli'] * 100,
            'antibiotic': ['Ciprofloxacin'] * 100,
            'week_start': pd.date_range('2024-06-01', periods=100)
        })
        
        test_outcomes = test_features.copy()
        test_outcomes['y_true'] = [0, 1] * 50
        
        # 3. Run Backtest Engine
        evaluator = BacktestEngine(session)
        horizon = 1
        
        results = evaluator.run_window_evaluation(
            model_metadata=model_metadata,
            test_features_df=test_features,
            test_outcomes_df=test_outcomes,
            horizon_weeks=horizon,
            dataset_version=dataset_version
        )
        
        logger.info("Evaluation Complete. Storing Results...")
        
        # 4. Save to DB (In production, use batch inserts)
        # Here we just log success for prototype
        
        run_id = results['run_metadata']['evaluation_id']
        logger.info(f"✅ Evaluation Run Recorded: {run_id}")
        logger.info(f"   Metrics: {len(results['metrics'])} rows (inc. Baseline/Calibrated)")
        logger.info(f"   Failures Logged: {len(results['failures'])} cases")
        
    except Exception as e:
        logger.error(f"Evaluation Failed: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    # Example usage
    run_evaluation(model_id="mock-uuid", dataset_version="v2-freeze")
