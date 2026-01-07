
"""
STP Stage 2: Ward Profile Builder
---------------------------------
Constructs static 'fingerprints' of resistance for each ward.
Used for risk stratification and IPC comparison.
"""

import pandas as pd
import numpy as np

def build_ward_profiles(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes ward-level resistance profiles.
    
    Returns DataFrame with:
    - ward
    - organism
    - antibiotic
    - mean_resistance
    - std_resistance (volatility over time if time data provided, otherwise broad std)
    - coverage_percent
    """
    
    # Filter valid AST
    df_valid = df[df['ast_result'].isin(['S', 'I', 'R'])].copy()
    
    # Calculate Total Isolates per Ward-Organism (for Coverage Denominator)
    # Dedup by isolate_id
    ward_org_counts = df.drop_duplicates('isolate_id').groupby(['ward', 'organism']).size().reset_index(name='total_isolates')
    
    # Calculate Resistance Stats per Ward-Organism-Antibiotic
    # We aggregate binary resistance for mean
    df_valid['is_R'] = (df_valid['ast_result'] == 'R').astype(int)
    
    stats = df_valid.groupby(['ward', 'organism', 'antibiotic']).agg(
        tested_count=('isolate_id', 'count'),
        resistant_count=('is_R', 'sum'),
        mean_resistance=('is_R', 'mean')
    ).reset_index()
    
    # Merge for Coverage
    merged = pd.merge(stats, ward_org_counts, on=['ward', 'organism'], how='left')
    merged['coverage_percent'] = (merged['tested_count'] / merged['total_isolates']) * 100.0
    
    # Cap 100% due to potential data anomalies (though logic should hold)
    merged['coverage_percent'] = merged['coverage_percent'].clip(upper=100.0)
    
    return merged[['ward', 'organism', 'antibiotic', 'mean_resistance', 'coverage_percent', 'tested_count']]
