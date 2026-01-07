
"""
STP Stage 3: Signal Detection Engine
------------------------------------
Detects statistical anomalies and step changes in resistance rates.
Methods: CUSUM (Cumulative Sum Control Chart), Bayesian Change Point.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any

def compute_cusum_signal(
    series: pd.Series, 
    mean_target: float = None, 
    std_dev: float = None,
    k: float = 0.5, # allowance (slack)
    h: float = 4.0  # decision interval (threshold)
) -> pd.DataFrame:
    """
    Computes Tabular CUSUM (Upper Sensitivity for Increases).
    """
    if series.empty:
        return pd.DataFrame()
        
    if mean_target is None:
        mean_target = series.mean()
    if std_dev is None:
        std_dev = series.std()
        if std_dev == 0:
            std_dev = 1e-6 # avoid division by zero
            
    # Normalize (Z-score like)
    z = (series - mean_target) / std_dev
    
    # Calculate C+ (Upper CUSUM)
    # C+[i] = max(0, z[i] - k + C+[i-1])
    
    upper_cusum = np.zeros(len(series))
    
    for i in range(1, len(series)):
        val = upper_cusum[i-1] + z.iloc[i] - k
        upper_cusum[i] = max(0, val)
        
    # Signal Strength is the raw CUSUM value.
    # Alert if > h.
    
    return pd.DataFrame({
        'week_start': series.index, # Assuming index is time, or caller handles mapping
        'cusum_score': upper_cusum,
        'is_alert': upper_cusum > h
    })

def bayesian_change_point_detection(series: pd.Series, hazard: float = 0.01) -> float:
    """
    Simplified Bayesian Online Change Point Detection (BOCPD) placeholder.
    Returns the Probability of a Change Point at the MOST RECENT time step.
    
    For prototype, we might use a simpler derivative check or naive impl.
    Reliable BOCPD requires 'bocd' library or complex implementation.
    
    Heuristic Fallback:
    Check if recent mean (last 2 weeks) > historical mean + 2 sigma.
    Returns probability estimation.
    """
    
    if len(series) < 5:
        return 0.0
        
    recent = series.iloc[-2:]
    historical = series.iloc[:-2]
    
    mu_hist = historical.mean()
    std_hist = historical.std()
    
    if std_hist == 0:
        return 0.0
        
    mu_recent = recent.mean()
    
    z_score = (mu_recent - mu_hist) / std_hist
    
    # Convert Z to probability (roughly)
    # Z=2 -> 97.7% -> p(change) ~ 0.95
    # Z=3 -> 99.9%
    
    if z_score < 0:
        return 0.0
        
    # Clip to [0, 1]
    # Simple sigmoid map
    prob = 1 / (1 + np.exp(-(z_score - 2))) # center at Z=2
    return float(prob)

