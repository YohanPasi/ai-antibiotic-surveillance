
"""
STP Stage 3: Model Drift Engine (M35)
------------------------------------
Monitors Population Stability Index (PSI) and prediction shifts.
ENFORCES M35: Automated tracking of drift.
"""

import numpy as np
import pandas as pd
from typing import Tuple

def calculate_psi(expected: np.ndarray, actual: np.ndarray, buckets: int = 10) -> float:
    """
    Calculates Population Stability Index (PSI) between two distributions.
    
    Args:
        expected: Baseline distribution (e.g., Training set probabilities).
        actual: Current distribution (e.g., Inference batch probabilities).
        buckets: Number of quantiles/bins.
        
    Returns:
        PSI score.
        < 0.1: No significant shift.
        0.1 - 0.25: Moderate shift.
        > 0.25: Significant shift.
    """
    
    def scale_range(input, min_v, max_v):
        input += -(np.min(input))
        input /= np.max(input) / (max_v - min_v)
        input += min_v
        return input

    breakpoints = np.arange(0, buckets + 1) / (buckets) * 100
    
    # Check simple range
    if len(expected) == 0 or len(actual) == 0:
        return 0.0
        
    # Percentiles for baseline
    # We use percentiles from 'expected' to define bins
    # For probabilities [0,1], we can use fixed bins or quantile bins.
    # Fixed bins [0, 0.1, ... 1.0] are safer for probabilities.
    
    bins = np.linspace(0, 1, buckets + 1)
    
    expected_percents = np.histogram(expected, bins=bins)[0] / len(expected)
    actual_percents = np.histogram(actual, bins=bins)[0] / len(actual)
    
    # Avoid div by zero
    expected_percents = np.where(expected_percents == 0, 0.0001, expected_percents)
    actual_percents = np.where(actual_percents == 0, 0.0001, actual_percents)
    
    psi_values = (expected_percents - actual_percents) * np.log(expected_percents / actual_percents)
    psi = np.sum(psi_values)
    
    return float(psi)

def detect_drift(psi_score: float) -> bool:
    """Returns True if PSI indicates significant drift (> 0.25)."""
    return psi_score > 0.25
