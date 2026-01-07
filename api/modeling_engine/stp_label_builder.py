
"""
STP Stage 3: Label Builder (M31)
-------------------------------
Generates target labels for predictive modeling.
ENFORCES M31: Labels derived ONLY from future resistance rates (T+h).
Strict anti-leakage checks.
"""

import pandas as pd
import numpy as np
from datetime import timedelta
from typing import Tuple

def build_future_labels(
    feature_df: pd.DataFrame,
    resistance_rates_df: pd.DataFrame,
    horizon_weeks: int,
    resistance_threshold: float = 0.30
) -> pd.DataFrame:
    """
    Attaches future resistance labels to feature snapshots.
    
    Args:
        feature_df: The frozen feature store snapshots (at time T).
        resistance_rates_df: The source of truth for resistance rates (containing T+h).
        horizon_weeks: The forecast horizon (h) in weeks.
        resistance_threshold: The threshold to define binary risk (theta).
        
    Returns:
        DataFrame with 'label_risk_binary', 'label_future_rate', 'target_date'.
    """
    
    # Validation M31
    if horizon_weeks < 1:
        raise ValueError("Horizon must be >= 1 week.")
        
    if 'week_start' not in feature_df.columns:
        raise ValueError("Feature DataFrame must have 'week_start' column.")
        
    # Prepare merge
    # T_target = T_feature + h weeks
    features = feature_df.copy()
    features['target_date'] = features['week_start'] + pd.Timedelta(weeks=horizon_weeks)
    
    # We join computed target labels from resistance_rates_df onto features based on (Ward, Organism, Antibiotic, TargetDate)
    # The rates df must have 'week_start' match 'target_date'
    
    targets = resistance_rates_df[['ward', 'organism', 'antibiotic', 'week_start', 'resistance_rate']].copy()
    targets.rename(columns={'week_start': 'target_date', 'resistance_rate': 'future_rate'}, inplace=True)
    
    # Merge
    merged = pd.merge(
        features,
        targets,
        on=['ward', 'organism', 'antibiotic', 'target_date'],
        how='left' # Left join: we want labels for our features. If future data missing, label is NaN.
    )
    
    # Generate Binary Label
    merged['label_risk_binary'] = (merged['future_rate'] >= resistance_threshold).astype(int)
    
    # Handle Missing Future Data (e.g., end of dataset)
    # If future_rate is NaN, label should be NaN (validity mask)
    merged.loc[merged['future_rate'].isna(), 'label_risk_binary'] = np.nan
    
    # Leakage Assertion (M31)
    # Ensure invalid/negative horizons didn't creep in
    leakage_check = (merged['target_date'] <= merged['week_start'])
    if leakage_check.any():
        affected = merged[leakage_check]
        raise ValueError(f"CRITICAL LEAKAGE DETECTED (M31): Target date <= Feature date. {len(affected)} rows.")
        
    return merged

def assert_no_leakage(df: pd.DataFrame, feature_col='week_start', target_col='target_date'):
    """Explicitly verifies M31 compliance on a labeled dataset."""
    if (df[target_col] <= df[feature_col]).any():
        raise ValueError("M31 VIOLATION: Future target leaks into feature window.")
    return True
