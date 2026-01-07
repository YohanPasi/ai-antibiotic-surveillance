
"""
STP Stage 2: Antibiotic Pressure Engine (M17)
--------------------------------------------
Calculates ecological metrics of antibiotic exposure.
Enforces M17 (Availability Bias Control).
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple

def calculate_shannon_index(counts: np.ndarray) -> float:
    """
    Calculates Shannon Diversity Index.
    H = -sum(p * ln(p))
    """
    total = counts.sum()
    if total == 0:
        return 0.0
    proportions = counts / total
    # Filter non-zero to avoid log(0)
    proportions = proportions[proportions > 0]
    return -np.sum(proportions * np.log(proportions))

def calculate_simpson_index(counts: np.ndarray) -> float:
    """
    Calculates Simpson's Index (D).
    D = sum(n*(n-1)) / (N*(N-1))
    Where this implementation is 1 - D (Diversity Index) usually.
    Standard Simpson: D = sum(p^2)
    Gini-Simpson: 1 - D
    Here we calculate Gini-Simpson (Diversity).
    """
    total = counts.sum()
    if total <= 1:
        return 0.0
    proportions = counts / total
    return 1.0 - np.sum(proportions ** 2)

def compute_pressure_metrics(
    df: pd.DataFrame, 
    group_cols: List[str] = ['ward'],
    min_coverage_threshold: float = 0.20 # M17: 20% coverage threshold
) -> pd.DataFrame:
    """
    Computes Exposure Density and Diversity Indices.
    Applies M17: Excludes rare antibiotics from diversity calculation.
    """
    
    # 1. Exposure Density = Total Tests / Total Isolates
    # Count total tests per group
    # Count total unique isolates per group
    
    # We rely on 'tested_count' summary or raw rows?
    # Using raw df input
    
    group_test_counts = df.groupby(group_cols).size().reset_index(name='total_tests')
    group_isolate_counts = df.groupby(group_cols)['isolate_id'].nunique().reset_index(name='total_isolates')
    
    metrics = pd.merge(group_test_counts, group_isolate_counts, on=group_cols)
    metrics['exposure_density'] = metrics['total_tests'] / metrics['total_isolates']
    
    # 2. Diversity Logic with M17
    # For each group, we need counts per antibiotic
    
    # Pivot: Index=Group, Col=Antibiotic, Val=Count
    abx_counts = df.groupby(group_cols + ['antibiotic']).size().reset_index(name='count')
    
    diversity_results = []
    
    # Iterate groups to filter locally (M17 is local bias control usually, or global?)
    # "Antibiotic Availability Bias Control ... computed only for antibiotics with coverage >= threshold"
    # Usually this means if an antibiotic is rarely tested in a Ward, don't let it skew the Ward's diversity.
    
    # We need total isolates per group to calculate coverage per antibiotic
    abx_metrics = pd.merge(abx_counts, group_isolate_counts, on=group_cols)
    abx_metrics['coverage'] = abx_metrics['count'] / abx_metrics['total_isolates']
    
    # Iterate over unique groups
    # This might be slow if many groups, but typically < 50 wards.
    unique_groups = metrics[group_cols].drop_duplicates()
    
    for _, group_row in unique_groups.iterrows():
        # Filter for this group
        # Construct mask
        mask = pd.Series(True, index=abx_metrics.index)
        for col in group_cols:
            mask &= (abx_metrics[col] == group_row[col])
            
        group_abx = abx_metrics[mask]
        
        # M17 Filter
        valid_abx = group_abx[group_abx['coverage'] >= min_coverage_threshold]
        rejected_abx = group_abx[group_abx['coverage'] < min_coverage_threshold]['antibiotic'].tolist()
        
        counts_array = valid_abx['count'].values
        
        shannon = calculate_shannon_index(counts_array)
        simpson = calculate_simpson_index(counts_array)
        
        res = {col: group_row[col] for col in group_cols}
        res.update({
            'shannon_index': shannon,
            'simpson_index': simpson,
            'excluded_antibiotics': rejected_abx # M17 Log
        })
        diversity_results.append(res)
        
    diversity_df = pd.DataFrame(diversity_results)
    
    final_df = pd.merge(metrics, diversity_df, on=group_cols)
    return final_df
