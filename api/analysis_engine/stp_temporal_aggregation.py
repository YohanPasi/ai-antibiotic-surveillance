
"""
STP Stage 2: Temporal Aggregation Engine (M13, M16)
--------------------------------------------------
Handles time-window binning and temporal integrity.
Enforces M13 (Temporal Firewall) and M16 (Partial Window Flagging).
"""

import pandas as pd
import numpy as np
from typing import Tuple, List

def get_iso_week_start(date: pd.Timestamp) -> pd.Timestamp:
    """Returns the Monday of the ISO week for a given date."""
    return date - pd.Timedelta(days=date.dayofweek)

def assert_no_future_leakage(df: pd.DataFrame, reference_date: pd.Timestamp):
    """
    M13: Temporal Firewall.
    Raises error if any data in df is strictly after reference_date.
    """
    if df.empty:
        return
        
    # Ensure sample_date is datetime
    if not pd.api.types.is_datetime64_any_dtype(df['sample_date']):
        df['sample_date'] = pd.to_datetime(df['sample_date'])
        
    max_date = df['sample_date'].max()
    if max_date > reference_date:
        raise ValueError(
            f"Temporal Leakage Detected! Data contains records from {max_date} "
            f"which is after the reference date {reference_date}."
        )

def calculate_coverage_days(
    window_start: pd.Timestamp,
    window_end: pd.Timestamp,
    dataset_start: pd.Timestamp,
    dataset_end: pd.Timestamp
) -> int:
    """
    Calculates number of days the window overlaps with the dataset range.
    """
    overlap_start = max(window_start, dataset_start)
    overlap_end = min(window_end, dataset_end)
    
    if overlap_start > overlap_end:
        return 0
    
    # +1 because inclusive
    return (overlap_end - overlap_start).days + 1

def flag_partial_windows(
    df_agg: pd.DataFrame, 
    time_col: str, 
    freq: str, 
    dataset_start: pd.Timestamp, 
    dataset_end: pd.Timestamp
) -> pd.DataFrame:
    """
    M16: Partial Window Handling.
    Adds 'is_partial_window' and 'coverage_days' to aggregated dataframe.
    """
    df_out = df_agg.copy()
    
    # Calculate window end based on freq
    # W-MON means Week starting Monday. Pandas DateOffset for Week usually adds 1 week.
    if freq == 'W-MON':
         # Window = [start, start + 6 days]
         # We can't vectorise everything cleanly with Timestamp objects in a lambda if efficient, 
         # but for reporting aggregate rows (usually <1000s), apply is fine.
        window_duration = pd.Timedelta(days=6)
    elif freq == 'MS':
        # Month Start. End is last day of month.
        # This is harder to vectorize directly with simple Timedelta.
        pass
    else:
        raise ValueError(f"Unsupported frequency: {freq}")
        
    def get_window_end(start_date):
        if freq == 'W-MON':
            return start_date + pd.Timedelta(days=6)
        elif freq == 'MS':
            # End of month
            return start_date + pd.offsets.MonthEnd(0)
        return start_date

    # Apply logic row-wise (robust)
    results = []
    for idx, row in df_out.iterrows():
        start = row[time_col]
        end = get_window_end(start)
        
        coverage = calculate_coverage_days(start, end, dataset_start, dataset_end)
        
        # Full window duration
        full_days = (end - start).days + 1
        
        is_partial = coverage < full_days
        
        results.append({
            'coverage_days': coverage,
            'is_partial_window': is_partial
        })
        
    meta_df = pd.DataFrame(results, index=df_out.index)
    df_out['coverage_days'] = meta_df['coverage_days']
    df_out['is_partial_window'] = meta_df['is_partial_window']
    
    return df_out

def aggregate_by_window(
    df: pd.DataFrame,
    freq: str = 'W-MON' # Weekly starting Monday
) -> pd.DataFrame:
    """
    Assigns a time window to each row.
    Returns DataFrame with 'week_start' or 'month_start' column.
    """
    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df['sample_date']):
        df['sample_date'] = pd.to_datetime(df['sample_date'])
        
    if freq == 'W-MON':
        # Normalize to Monday
        df['time_window'] = df['sample_date'].apply(lambda x: x - pd.Timedelta(days=x.dayofweek))
        # Ensure time component is zero
        df['time_window'] = df['time_window'].dt.normalize()
    elif freq == 'MS':
        # Normalize to Month Start
        df['time_window'] = df['sample_date'].dt.to_period('M').dt.to_timestamp()
    else:
        raise ValueError("Frequency must be 'W-MON' or 'MS'")
        
    return df
