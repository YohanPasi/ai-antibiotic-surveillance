
"""
STP Stage 4: Metrics Engine (M44, M53)
--------------------------------------
Calculates priority metrics and clinical error costs.
ENFORCES M44: NPV > Sensitivity > FNR.
ENFORCES M53: Clinical Cost Reporting.
"""

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, precision_score, recall_score, roc_auc_score, confusion_matrix

def compute_priority_metrics(
    y_true: pd.Series, 
    y_prob: pd.Series, 
    threshold: float = 0.5
) -> dict:
    """
    Calculates M44 Priority Metrics.
    """
    y_pred = (y_prob >= threshold).astype(int)
    
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    
    # 1. NPV (Negative Predictive Value) - The Safety Net
    npv = tn / (tn + fn) if (tn + fn) > 0 else 0.0
    
    # 2. Sensitivity (Recall) - The Detection Power
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    
    # 3. False Negative Rate (Miss Rate)
    fnr = fn / (tp + fn) if (tp + fn) > 0 else 0.0
    
    # 4. Calibration (Brier Score)
    brier = brier_score_loss(y_true, y_prob)
    
    # Secondary
    try:
        auroc = roc_auc_score(y_true, y_prob)
    except ValueError:
        auroc = np.nan # Requires both classes
        
    return {
        "NPV": float(npv),
        "Sensitivity": float(sensitivity),
        "FNR": float(fnr),
        "Brier_Score": float(brier),
        "AUROC": float(auroc),
        "TN": int(tn),
        "FP": int(fp),
        "FN": int(fn),
        "TP": int(tp)
    }

def compute_clinical_cost_score(
    metrics: dict,
    cost_per_miss: float = 10.0, # Weight for FN
    cost_per_false_alarm: float = 1.0 # Weight for FP
) -> float:
    """
    M53: Clinical Error Cost Framing.
    Score = (FN * Cost_FN) + (FP * Cost_FP) (Lower is better).
    Normalized per 100 cases for comparability.
    """
    fn = metrics.get('FN', 0)
    fp = metrics.get('FP', 0)
    total = metrics.get('TN', 0) + metrics.get('TP', 0) + fn + fp
    
    if total == 0:
        return 0.0

    raw_cost = (fn * cost_per_miss) + (fp * cost_per_false_alarm)
    normalized_cost = (raw_cost / total) * 100
    
    return float(normalized_cost)
