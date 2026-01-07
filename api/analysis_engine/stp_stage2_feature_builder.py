
"""
STP Stage 2: Feature Store Builder (M14, M19)
--------------------------------------------
Aggregates all Stage 2 signals into a single, immutable feature store.
Enforces M14 (Feature Immutability) and M19 (Snapshot Freezing).
"""

import pandas as pd
import numpy as np
import uuid
from datetime import datetime
from typing import Optional

def generate_stage2_version_id() -> str:
    """Generates a unique version ID for a Stage 2 snapshot."""
    # format: v2-YYYYMMDD-HHMMSS-UUID
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"v2-{timestamp}-{unique_id}"

def build_feature_store_snapshot(
    weekly_rates_df: pd.DataFrame,
    temporal_trends_df: Optional[pd.DataFrame],
    ward_pressure_df: Optional[pd.DataFrame],
    stage1_version: str,
    stage2_version: str = None
) -> pd.DataFrame:
    """
    Joins all signal components into the canonical Feature Store Record.
    
    Args:
        weekly_rates_df: Core resistance data (organism, antibiotic, ward, week_start).
        temporal_trends_df: Trend signals (organism, antibiotic, ward, week_start).
        ward_pressure_df: Ecological pressure (ward, week_start).
        stage1_version: The frozen Stage 1 version this is derived from.
        stage2_version: The unique ID for this Stage 2 run.
        
    Returns:
        DataFrame matching `stp_stage2_feature_store` schema.
    """
    
    if stage2_version is None:
        stage2_version = generate_stage2_version_id()
        
    # Start with the backbone: Weekly Rates
    # Ensure key columns exist
    key_cols = ['organism', 'antibiotic', 'ward', 'week_start']
    for col in key_cols:
        if col not in weekly_rates_df.columns:
            raise ValueError(f"Weekly rates dataframe missing key column: {col}")
            
    # Base Feature DF
    feature_df = weekly_rates_df.copy()
    
    # 1. Join Temporal Trends (Left Join)
    if temporal_trends_df is not None and not temporal_trends_df.empty:
        # Check keys
        feature_df = pd.merge(
            feature_df,
            temporal_trends_df[['organism', 'antibiotic', 'ward', 'week_start', 'rolling_slope', 'volatility']],
            on=['organism', 'antibiotic', 'ward', 'week_start'],
            how='left'
        )
    else:
        # Add placeholders if no trends yet
        feature_df['rolling_slope'] = np.nan
        feature_df['volatility'] = np.nan
        
    # 2. Join Ward Pressure (Left Join - on Ward/Time only)
    if ward_pressure_df is not None and not ward_pressure_df.empty:
        # Assuming ward_pressure_df has 'ward', 'time_window_start' (as week_start for join)
        # We need to ensure column names match for join
        
        # Helper to rename if needed
        # In stp_antibiotic_pressure.py, we output 'time_window_start'
        pressure_join_df = ward_pressure_df.copy()
        if 'time_window_start' in pressure_join_df.columns and 'week_start' not in pressure_join_df.columns:
            pressure_join_df.rename(columns={'time_window_start': 'week_start'}, inplace=True)
            
        # Ensure Types match
        if not pd.api.types.is_datetime64_any_dtype(pressure_join_df['week_start']):
            pressure_join_df['week_start'] = pd.to_datetime(pressure_join_df['week_start'])
            
        feature_df = pd.merge(
            feature_df,
            pressure_join_df[['ward', 'week_start', 'exposure_density', 'shannon_index']],
            on=['ward', 'week_start'],
            how='left'
        )
    else:
        feature_df['exposure_density'] = np.nan
        feature_df['shannon_index'] = np.nan
        
    # 3. Add Governance Metadata (M14, M19)
    feature_df['stage2_version'] = stage2_version
    feature_df['derived_from_stage1_version'] = stage1_version
    feature_df['is_frozen'] = True # By definition, once built into this store, it's a frozen snapshot.
    
    # Select final columns to match Schema exactly
    # Schema: 
    # organism, antibiotic, ward, week_start, 
    # resistance_rate, tested_count, 
    # trend_slope (rolling_slope), volatility, 
    # exposure_density, shannon_index, 
    # is_stable, is_partial_window, 
    # stage2_version, derived_from_stage1_version, is_frozen
    
    # Rename rolling_slope -> trend_slope if needed by Schema
    # Schema says `trend_slope FLOAT`, `volatility FLOAT`
    # Our df has `rolling_slope`
    feature_df.rename(columns={'rolling_slope': 'trend_slope'}, inplace=True)
    
    # Return ordered columns
    final_cols = [
        'organism', 'antibiotic', 'ward', 'week_start',
        'resistance_rate', 'tested_count',
        'trend_slope', 'volatility',
        'exposure_density', 'shannon_index',
        'is_stable', 'is_partial_window',
        'stage2_version', 'derived_from_stage1_version', 'is_frozen'
    ]
    
    # Ensure all exist (fill NaN if missing - though join logic above should cover)
    for c in final_cols:
        if c not in feature_df.columns:
            feature_df[c] = np.nan
            
    return feature_df[final_cols]
