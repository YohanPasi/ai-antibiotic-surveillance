"""
STP Stage 1: Time Governance Utilities
=======================================
Purpose: Enforce temporal integrity and prevent data leakage

Functions:
- ISO week calculations
- Temporal split enforcement
- Future leakage validation

M10: Used by Stage 2+ to prevent data leakage
"""

from datetime import datetime, date, timedelta
from typing import Tuple
import pandas as pd


def get_week_start(input_date: date) -> date:
    """
    Get ISO week start (Monday) for a given date.
    
    Args:
        input_date: Any date
    
    Returns:
        Monday of that week
    """
    # ISO calendar: Monday = 1, Sunday = 7
    weekday = input_date.isoweekday()
    week_start = input_date - timedelta(days=weekday - 1)
    return week_start


def get_temporal_split(cutoff_date: date, data: pd.DataFrame, date_column: str = 'sample_date') -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split data into train/test based on cutoff date.
    
    Critical Rule (M10): At time t, only data where sample_date ≤ t is visible
    
    Args:
        cutoff_date: Split point
        data: DataFrame to split
        date_column: Name of date column
    
    Returns:
        (train_data, test_data) tuple
    """
    train = data[data[date_column] <= cutoff_date].copy()
    test = data[data[date_column] > cutoff_date].copy()
    
    return train, test


def assert_no_future_leakage(data: pd.DataFrame, reference_date: date, date_column: str = 'sample_date'):
    """
    Validate that no future information is present.
    
    M10: Critical for Stage 2+ compliance
    
    Args:
        data: DataFrame to validate
        reference_date: Reference point (e.g., "today" in simulation)
        date_column: Name of date column
    
    Raises:
        ValueError: If future data detected
    """
    if date_column not in data.columns:
        raise ValueError(f"Date column '{date_column}' not found in data")
    
    future_rows = data[data[date_column] > reference_date]
    
    if len(future_rows) > 0:
        raise ValueError(
            f"DATA LEAKAGE DETECTED: {len(future_rows)} rows with dates > {reference_date}\n"
            f"Earliest future date: {future_rows[date_column].min()}\n"
            f"This violates temporal integrity (M10 Stage Boundary)"
        )


def get_date_range_stats(data: pd.DataFrame, date_column: str = 'sample_date') -> dict:
    """
    Get temporal coverage statistics.
    
    Returns:
        Dictionary with date range info
    """
    return {
        'earliest_date': data[date_column].min(),
        'latest_date': data[date_column].max(),
        'total_days': (data[date_column].max() - data[date_column].min()).days,
        'unique_dates': data[date_column].nunique()
    }


# Example usage for documentation
if __name__ == "__main__":
    # Example: Get week start
    today = date.today()
    week_start = get_week_start(today)
    print(f"Today: {today}")
    print(f"Week start (Monday): {week_start}")
    
    # Example: Validate no future leakage
    sample_data = pd.DataFrame({
        'sample_date': pd.date_range('2024-01-01', periods=100, freq='D')
    })
    
    try:
        assert_no_future_leakage(sample_data, date(2024, 2, 1))
        print("✓ No future leakage detected")
    except ValueError as e:
        print(f"✗ {e}")
