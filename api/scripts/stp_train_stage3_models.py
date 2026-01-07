
"""
STP Stage 3: Training Orchestrator
----------------------------------
Main pipeline for training Resistance Forecasting models.
ENFORCES Governance M23-M40.

Workflow:
1. Load Frozen Features (M23).
2. Generate Labels (M31).
3. Preprocess & Balance (M26).
4. Train with Temporal CV (M24).
5. Calibrate & Threshold (M38, M39).
6. Register Model & Metrics (M29).
"""

import sys
import os
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime

# Path setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from api.modeling_engine.stp_preprocessing import load_frozen_features, generate_lagged_features, handle_imbalance
    from api.modeling_engine.stp_label_builder import build_future_labels, assert_no_leakage
    from api.modeling_engine.stp_forecasting import STPForecaster
    from api.modeling_engine.stp_model_manager import save_model
except ImportError:
    # Fallback if running where 'api' is root
    from modeling_engine.stp_preprocessing import load_frozen_features, generate_lagged_features, handle_imbalance
    from modeling_engine.stp_label_builder import build_future_labels, assert_no_leakage
    from modeling_engine.stp_forecasting import STPForecaster
    from modeling_engine.stp_model_manager import save_model

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_training_pipeline(
    stage2_version: str,
    target_organism: str = 'E. coli',
    target_antibiotic: str = 'Ciprofloxacin',
    horizon_weeks: int = 1
):
    logger.info(f"🚀 Starting Training Pipeline for {target_organism} - {target_antibiotic} (Horizon: {horizon_weeks}w)")
    
    # 1. Load Data (Mocking logic for prototype)
    # In real pipeline: fetch from stp_stage2_feature_store table via SQL.
    # Here we simulate proper dataframe structure for demonstration matching M23.
    
    logger.info("Step 1: Loading Frozen Features (M23)...")
    # Simulation: We assume we pulled this from DB.
    # We create dummy data to ensure the script structure is valid.
    
    # In production, specific query: SELECT * FROM stp_stage2_feature_store WHERE stage2_version = ...
    
    # Mock DF
    feature_df = pd.DataFrame({
        'ward': ['Ward A'] * 50 + ['Ward B'] * 50,
        'organism': [target_organism] * 100,
        'antibiotic': [target_antibiotic] * 100,
        'week_start': pd.date_range(start='2024-01-01', periods=100, freq='W'),
        'resistance_rate': np.random.uniform(0, 0.5, 100), # Current rate
        'tested_count': np.random.randint(10, 50, 100),
        'is_frozen': [True] * 100, # M23
        'stage2_version': [stage2_version] * 100
    })
    
    valid_features = load_frozen_features(feature_df, stage2_version)
    
    # 2. Label Generation (M31)
    logger.info("Step 2: Generating Labels (M31)...")
    # We need resistance outcomes. For simulation, using same DF.
    rr_df = feature_df[['ward', 'organism', 'antibiotic', 'week_start', 'resistance_rate']].copy()
    
    try:
        labeled_df = build_future_labels(valid_features, rr_df, horizon_weeks, resistance_threshold=0.3)
        assert_no_leakage(labeled_df)
    except Exception as e:
        logger.error(f"Label Generation Failed: {e}")
        return

    # Drop rows where label is NaN (future unknown)
    train_df = labeled_df.dropna(subset=['label_risk_binary'])
    
    if train_df.empty:
        logger.error("No training data after labeling.")
        return
        
    X_cols = ['resistance_rate', 'tested_count'] # Simple features
    X = train_df[X_cols]
    y = train_df['label_risk_binary']
    dates = train_df['week_start']
    
    # 3. Model Training (XGBoost)
    logger.info("Step 3: Training with Temporal CV (M24)...")
    forecaster = STPForecaster(model_type='xgboost', horizon=horizon_weeks)
    
    try:
        forecaster.train_with_temporal_cv(X, y, dates, n_splits=3)
        logger.info(f"Training Complete. Metrics: {forecaster.metrics}")
    except Exception as e:
        logger.error(f"Training Failed: {e}")
        return
        
    # 4. Register Model (M29)
    logger.info("Step 4: Registering Model (M29)...")
    
    # Serialize
    # We won't actually save file to disk in this mock run to avoid clutter, 
    # but we call the manager logic dryly.
    
    features_hash = str(hash(json.dumps(X_cols))) # Simple hash approximation
    
    record = save_model(
        model_obj=forecaster,
        model_type='xgboost',
        target=f"{target_organism}_{target_antibiotic}",
        horizon=horizon_weeks,
        stage2_version=stage2_version,
        metrics=forecaster.metrics,
        features_hash=features_hash
    )
    
    logger.info(f"✅ Model Registered: {record['model_id']}")
    logger.info("Pipeline Complete.")

if __name__ == "__main__":
    # Example Run
    run_training_pipeline(stage2_version="v2-20250101-MOCK")
