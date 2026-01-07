
"""
STP Stage 3: Uncertainty Quantification (M33)
--------------------------------------------
Calculates confidence intervals for predictions.
ENFORCES M33: All predictions MUST have uncertainty bounds.
"""

import numpy as np
import pandas as pd
from typing import Tuple, List

def compute_bootstrap_intervals(
    model, 
    X: pd.DataFrame, 
    n_bootstraps: int = 20, # Keep low for performance in prototype 
    alpha: float = 0.05
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Estimates 95% CI using Bootstrap Aggregation (Bagging) uncertainty.
    
    Args:
        model: Trained model (sklearn interface).
        X: Feature matrix.
        n_bootstraps: Number of bootstrap iterations.
        alpha: Significance level (default 0.05 for 95% CI).
        
    Returns:
        (lower_ci, upper_ci) arrays.
    """
    preds = []
    
    # In a true bootstrap, we would retrain the model on bootstrapped data N times.
    # However, for inference-time uncertainty on a SINGLE trained model, 
    # we might use Dropouts (DNN) or Tree variance (Random Forest/XGB).
    
    # If the model is a Tree Ensemble (RF/XGB), we can get predictions from individual estimators.
    # XGBoost: 'pred_contribs' or iterating trees is complex.
    
    # Alternative: Conformal Prediction or simple error modeling.
    # M33 asks for "Bootstrap or Quantile".
    # Since we are planning to use XGBoost, we can use Quantile Regression (train 3 models: q0.05, q0.5, q0.95).
    # OR we can assume Gaussian error around the probability (calibration).
    
    # Simple Approach for Prototype: 
    # If model supports it, use subsampling prediction.
    # Since we can't easily retrain 100 times for every request or batch,
    # we will plan to use QUANTILE REGRESSION in the main training loop.
    
    # However, this module provides the interface.
    # If we pass a list of models (bootstrapped ensemble), we can compute here.
    
    # Mocking behavior for single model if passed:
    # We can't fabricate uncertainty from a single point estimate without assumptions.
    # So we raise if not a list.
    
    if isinstance(model, list):
         # Ensemble of bootstraps
         for m in model:
             preds.append(m.predict_proba(X)[:, 1])
         
         preds_arr = np.array(preds)
         lower = np.quantile(preds_arr, alpha / 2, axis=0)
         upper = np.quantile(preds_arr, 1 - (alpha / 2), axis=0)
         return lower, upper
         
    else:
        # Fallback/Warning: Single model provided. 
        # Return NaN bounds? Or fixed margin? 
        # Governance M33 says "Must include CI".
        # We will assume the caller handles Quantile Regression models separately,
        # and this function is specifically for Bootstrap Ensembling.
        raise ValueError("Bootstrap intervals require a list of bootstrapped models.")

def compute_quantile_bounds(
    preds_lower: np.ndarray,
    preds_upper: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Trivial helper for Quantile Regression outputs.
    Ensures logical consistency (Lower <= Upper).
    """
    # Clip bounds to [0,1]
    lower = np.clip(preds_lower, 0, 1)
    upper = np.clip(preds_upper, 0, 1)
    
    # Enforce order
    # If crossed, take mean? Or clamp?
    # Usually shouldn't cross if trained well, but can happen.
    
    fixed_lower = np.minimum(lower, upper)
    fixed_upper = np.maximum(lower, upper)
    
    return fixed_lower, fixed_upper
