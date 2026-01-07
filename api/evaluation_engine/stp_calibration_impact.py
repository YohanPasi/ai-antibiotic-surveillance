
"""
STP Stage 4: Calibration Impact Assessment (M52)
-----------------------------------------------
Evaluates whether calibration improves clinical decision making.
ENFORCES M52: Comparison of Pre- vs Post-Calibration Metrics.
"""

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import brier_score_loss

# We assume we have access to compute_priority_metrics to fetch NPV/Sensitivity
from api.evaluation_engine.stp_metrics import compute_priority_metrics

def assess_calibration_impact(
    y_true: pd.Series,
    y_prob_raw: pd.Series,
    y_prob_calibrated: pd.Series,
    threshold: float = 0.5
) -> dict:
    """
    Computes delta in critical metrics (NPV) to prove calibration value.
    """
    
    metrics_raw = compute_priority_metrics(y_true, y_prob_raw, threshold)
    metrics_cal = compute_priority_metrics(y_true, y_prob_calibrated, threshold)
    
    # Calculate Deltas (Calibrated - Raw)
    # Ideally, Brier should decrease (improve), NPV should strictly non-decrease ideally (safety).
    
    delta_brier = metrics_cal['Brier_Score'] - metrics_raw['Brier_Score']
    delta_npv = metrics_cal['NPV'] - metrics_raw['NPV']
    delta_fnr = metrics_cal['FNR'] - metrics_raw['FNR']
    
    return {
        "raw": metrics_raw,
        "calibrated": metrics_cal,
        "impact": {
            "delta_brier": delta_brier,
            "delta_npv": delta_npv,
            "delta_fnr": delta_fnr,
            "calibration_beneficial": delta_brier < 0 # Beneficial if Brier drops
        }
    }
