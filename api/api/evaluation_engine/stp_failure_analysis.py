
"""
STP Stage 4: Failure Analysis (M48)
-----------------------------------
Identifies and logs specific failure cases for manual audit.
ENFORCES M48: Explicit False Negative Logging.
"""

import pandas as pd

def extract_failure_cases(
    eval_df: pd.DataFrame,
    threshold: float = 0.5
) -> pd.DataFrame:
    """
    Identifies False Negatives (Missed) and False Positives (False Alarms).
    """
    
    df = eval_df.copy()
    df['predicted_label'] = (df['y_prob'] >= threshold).astype(int)
    
    # False Negative: Predicted 0, Actual 1 (High Risk Missed)
    mask_fn = (df['predicted_label'] == 0) & (df['y_true'] == 1)
    
    # False Positive: Predicted 1, Actual 0 (False Alarm)
    mask_fp = (df['predicted_label'] == 1) & (df['y_true'] == 0)
    
    failures = df[mask_fn | mask_fp].copy()
    
    failures['failure_type'] = failures.apply(
        lambda row: 'FN' if row['y_true'] == 1 else 'FP', axis=1
    )
    
    # Heuristic Reason (M48 metadata)
    # Low N? Drift? Boundary?
    # For prototype, we check if probs was "close" to threshold (Boundary)
    
    def get_reason(row):
        prob = row['y_prob']
        if abs(prob - threshold) < 0.10:
            return 'boundary_case'
        if row['failure_type'] == 'FN' and prob < 0.1:
            return 'severe_miss' # Model very confident it was safe
        return 'standard_error'
        
    failures['reason'] = failures.apply(get_reason, axis=1)
    
    # Return structured for DB Insert
    # Needs: ward, organism, antibiotic, week_date, predicted_prob, actual_outcome
    return failures[['ward', 'organism', 'antibiotic', 'week_start', 'y_prob', 'y_true', 'failure_type', 'reason']]
