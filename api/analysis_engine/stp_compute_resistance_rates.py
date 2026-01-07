
"""
STP Stage 2: Resistance Rate Engine (M11, M12, M15, M21, M22)
------------------------------------------------------------
Computes epidemiological resistance rates from validated AST data.
Strictly adheres to governance policies for denominator handling and suppression.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Any

# M12: Minimum sample threshold
DEFAULT_MIN_SAMPLE_THRESHOLD = 30

def compute_resistance_metrics(
    df_chunk: pd.DataFrame, 
    min_threshold: int = DEFAULT_MIN_SAMPLE_THRESHOLD
) -> Dict[str, Any]:
    """
    Computes resistance metrics for a specific group (e.g., one antibiotic in one ward).
    
    Args:
        df_chunk: DataFrame containing 'ast_result' column for a single group.
        min_threshold: Minimum N required for stability (M12).
        
    Returns:
        Dictionary containing:
        - resistance_rate (float or None)
        - tested_count (int)
        - susceptible_count (int)
        - intermediate_count (int)
        - resistant_count (int)
        - is_stable (bool)
        - suppression_reason (str or None)
    """
    
    # M21: Explicit Tested Count Logic - Strictly exclude NA
    # Filter valid results (S, I, R)
    valid_results = df_chunk[df_chunk['ast_result'].isin(['S', 'I', 'R'])]['ast_result']
    
    # Calculate counts
    s_count = int((valid_results == 'S').sum())
    i_count = int((valid_results == 'I').sum())
    r_count = int((valid_results == 'R').sum())
    
    # M11: Denominator Transparency
    tested_count = s_count + i_count + r_count
    
    # Initialize Rate and Flags
    resistance_rate: Optional[float] = None
    is_stable: bool = True
    suppression_reason: Optional[str] = None
    
    # M22: Zero/Suppression Policy
    if tested_count == 0:
        resistance_rate = None
        # Inherently unstable/undefined, but usually we don't store 0-count rows in aggregations
        # If we do store them, is_stable=False is appropriate.
        is_stable = False
        suppression_reason = 'NO_DATA'
    else:
        # M15: Intermediate Handling - 'I' is in Denominator (tested_count), NOT Numerator (r_count)
        # Rate = R / (S + I + R)
        resistance_rate = float(r_count) / float(tested_count)
        
        # M12/M22: Low Sample Threshold
        if tested_count < min_threshold:
            is_stable = False
            suppression_reason = 'LOW_SAMPLE_SIZE'
            
    return {
        "resistance_rate": resistance_rate,
        "tested_count": tested_count,
        "susceptible_count": s_count,
        "intermediate_count": i_count,
        "resistant_count": r_count,
        "is_stable": is_stable,
        "suppression_reason": suppression_reason
    }

def aggregate_resistance_rates(
    df: pd.DataFrame,
    group_cols: list,
    min_threshold: int = DEFAULT_MIN_SAMPLE_THRESHOLD
) -> pd.DataFrame:
    """
    Aggregates a larger dataframe by group_cols and computes metrics for each group.
    OPTIMIZED for performance using vectorization where possible, 
    but utilizing apply for complex M-logic if needed.
    """
    # Defensive check
    required_cols = ['ast_result'] + group_cols
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    # Preliminary filter for M21 (Exclude NA globally for speed, 
    # but keep track of structure if we need to report 0 counts)
    # Actually, we rely on groupby to handle missing groups or we iterate.
    # To ensure M21 is respected, we first filter out NAs.
    df_valid = df[df['ast_result'].isin(['S', 'I', 'R'])].copy()
    
    # Define aggregation logic
    # We can do this efficiently with pivot_table or groupby.agg
    
    # 1. Calculate Counts
    # Encode S, I, R as binaries for summing
    df_valid['is_S'] = (df_valid['ast_result'] == 'S').astype(int)
    df_valid['is_I'] = (df_valid['ast_result'] == 'I').astype(int)
    df_valid['is_R'] = (df_valid['ast_result'] == 'R').astype(int)
    
    agg_funcs = {
        'is_S': 'sum',
        'is_I': 'sum',
        'is_R': 'sum'
    }
    
    grouped = df_valid.groupby(group_cols).agg(agg_funcs).reset_index()
    
    # Rename columns
    grouped.rename(columns={
        'is_S': 'susceptible_count',
        'is_I': 'intermediate_count',
        'is_R': 'resistant_count'
    }, inplace=True)
    
    # 2. Derive Metrics (Vectorized M15, M11, M22)
    grouped['tested_count'] = grouped['susceptible_count'] + grouped['intermediate_count'] + grouped['resistant_count']
    
    # M15 Calculation
    grouped['resistance_rate'] = grouped['resistant_count'] / grouped['tested_count']
    
    # M12/M22 Flags
    grouped['is_stable'] = grouped['tested_count'] >= min_threshold
    grouped['suppression_reason'] = np.where(
        grouped['tested_count'] < min_threshold, 
        'LOW_SAMPLE_SIZE', 
        None
    )
    
    return grouped
