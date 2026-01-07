
"""
STP Stage 4: Calibration Engine (M46)
-------------------------------------
Generates Reliability Curves (Observed vs Predicted).
ENFORCES M46: Calibration Verification.
"""

import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve

def compute_calibration_curve_data(
    y_true: pd.Series,
    y_prob: pd.Series,
    n_bins: int = 10
) -> pd.DataFrame:
    """
    Computes points for the reliability diagram.
    Returns DataFrame with [bin_index, prob_pred, prob_true, count].
    """
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=n_bins, strategy='uniform')
    
    # To get counts per bin, we can replicate the binning logic
    # calibration_curve doesn't return counts directly.
    
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    binids = np.digitize(y_prob, bins) - 1
    
    # Adjust last bin edge case
    binids = np.clip(binids, 0, n_bins - 1)
    
    results = []
    
    for i in range(n_bins):
        mask = (binids == i)
        count = mask.sum()
        if count > 0:
            obs = y_true[mask].mean()
            pred = y_prob[mask].mean()
            results.append({
                "bin_index": i,
                "predicted_prob_mean": float(pred),
                "observed_rate": float(obs),
                "sample_count": int(count)
            })
            
    return pd.DataFrame(results)
