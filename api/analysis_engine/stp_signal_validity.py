
"""
STP Stage 2: Signal Validity Engine
-----------------------------------
Calculates advanced signal stability metrics (volatility, trend consistency).
Complements the basic N-threshold stability checks from the Rate Engine.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any

def calculate_volatility(
    series: pd.Series, 
    window: int = 4
) -> pd.Series:
    """
    Calculates rolling standard deviation as a proxy for volatility.
    """
    # Min periods = window / 2 to allow some missingness but not too much
    return series.rolling(window=window, min_periods=max(2, window // 2)).std()

def detect_change_points(
    series: pd.Series,
    threshold_std: float = 3.0
) -> pd.Series:
    """
    Simple change point detection using Z-score of week-over-week changes.
    Returns boolean series.
    """
    pct_change = series.diff()
    mean_change = pct_change.mean()
    std_change = pct_change.std()
    
    if std_change == 0 or pd.isna(std_change):
        return pd.Series(False, index=series.index)
        
    z_scores = (pct_change - mean_change) / std_change
    return z_scores.abs() > threshold_std

def assess_signal_stability(
    resistance_series: pd.Series,
    tested_counts_series: pd.Series,
    min_tested_threshold: int = 30,
    volatility_threshold: float = 0.15 # 15% rate swing std dev
) -> pd.Series:
    """
    Composite stability score.
    Stable if:
    1. Sample size >= threshold (Basic)
    2. Volatility < volatility_threshold (Advanced)
    """
    
    # 1. Sample Size Check
    size_stable = tested_counts_series >= min_tested_threshold
    
    # 2. Volatility Check
    volatility = calculate_volatility(resistance_series)
    vol_stable = (volatility < volatility_threshold) | volatility.isna()
    
    # If volatility is NaN (not enough data), we default to True for this component 
    # unless sample size is small, which is caught by size_stable.
    
    return size_stable & vol_stable
