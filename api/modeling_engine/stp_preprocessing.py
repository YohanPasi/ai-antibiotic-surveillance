
"""
STP Stage 3: Preprocessing (M23, M26)
--------------------------------------
Feature Engineering for time-series forecasting.
ENFORCES M23: Reads strictly from frozen Stage 2 features.
ENFORCES M26: Explicit class imbalance handling.
"""

import pandas as pd
import numpy as np
from typing import List, Optional

def load_frozen_features(
    feature_store_df: pd.DataFrame, 
    stage2_version: str
) -> pd.DataFrame:
    """
    M23: Validates input is from Frozen Stage 2 Store.
    """
    if 'is_frozen' not in feature_store_df.columns:
         raise ValueError("M23 VIOLATION: Input is not a valid Feature Store (missing 'is_frozen').")
         
    frozen_check = feature_store_df['is_frozen'].all()
    if not frozen_check:
         raise ValueError("M23 VIOLATION: Input contains non-frozen records.")
         
    # Filter by specific version if provided? Or ensure consistent usage.
    # For now, just usage check.
    return feature_store_df.copy()

def generate_lagged_features(
    df: pd.DataFrame, 
    group_cols: List[str], 
    value_cols: List[str], 
    lags: List[int]
) -> pd.DataFrame:
    """
    Generates time-lagged features (T-1, T-2...).
    df must be sorted by time.
    """
    df = df.sort_values(by=group_cols + ['week_start'])
    
    for lag in lags:
        for col in value_cols:
            lag_name = f"{col}_lag{lag}"
            df[lag_name] = df.groupby(group_cols)[col].shift(lag)
            
    return df

def handle_imbalance(
    X: pd.DataFrame, 
    y: pd.Series, 
    method: str = 'class_weight'
):
    """
    M26: Explicit Class Imbalance Handling.
    Options: 'class_weight' (calculate scale), 'smote' (resample).
    
    Returns:
        If 'class_weight': (X, y, scale_pos_weight estimate)
        If 'smote': (X_resampled, y_resampled, None)
    """
    
    if method == 'class_weight':
        # Calculate ratio of Negative / Positive
        n_pos = y.sum()
        n_neg = len(y) - n_pos
        if n_pos == 0:
            return X, y, 1.0 # Edge case
        scale_pos_weight = n_neg / n_pos
        return X, y, scale_pos_weight
        
    elif method == 'smote':
        # Placeholder for SMOTE (requires imblearn dependency in env)
        # Assuming minimal env for now, raise if not present
        raise NotImplementedError("SMOTE requires 'imblearn' package. Use 'class_weight' for now.")
        
    else:
        raise ValueError(f"Unknown imbalance method: {method}")

