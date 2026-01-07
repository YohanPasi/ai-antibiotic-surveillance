
"""
STP Stage 4: Ward Stratified Evaluation (M45)
---------------------------------------------
Evaluates model performance across ward subgroups to detect bias.
ENFORCES M45: Stratified Reporting (ICU vs Non-ICU).
"""

import pandas as pd
import numpy as np
from api.evaluation_engine.stp_metrics import compute_priority_metrics

def compute_stratified_metrics(
    eval_df: pd.DataFrame,
    threshold: float = 0.5
) -> dict:
    """
    Computes priority metrics for ALL, ICU, and NON-ICU subgroups.
    Expects eval_df to have ['ward_type', 'y_true', 'y_prob'].
    """
    
    results = {}
    
    # 1. Global (ALL)
    results['ALL'] = compute_priority_metrics(eval_df['y_true'], eval_df['y_prob'], threshold)
    
    # 2. Stratified
    # Check if 'ward_type' exists. If not, maybe infer from ward name or skip?
    # Stage 1/2 didn't explicitly map ward types in DB schema in this prototype, 
    # but we can infer or pass it in.
    # For prototype, we'll assume a column or a mapper is available.
    
    if 'ward_type' in eval_df.columns:
        groups = eval_df['ward_type'].unique()
        for g in groups:
            subgroup = eval_df[eval_df['ward_type'] == g]
            if not subgroup.empty:
                results[g] = compute_priority_metrics(subgroup['y_true'], subgroup['y_prob'], threshold)
                
    else:
        # Fallback heuristic if ward_type missing
        # ICU often in name
        is_icu = eval_df['ward'].str.contains('ICU', case=False, na=False)
        
        icu_df = eval_df[is_icu]
        non_icu_df = eval_df[~is_icu]
        
        if not icu_df.empty:
            results['ICU'] = compute_priority_metrics(icu_df['y_true'], icu_df['y_prob'], threshold)
        if not non_icu_df.empty:
            results['NON_ICU'] = compute_priority_metrics(non_icu_df['y_true'], non_icu_df['y_prob'], threshold)
            
    return results
