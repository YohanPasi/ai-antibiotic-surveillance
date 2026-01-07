
"""
STP Stage 2: Unit Tests (Governance & Logic Verification)
---------------------------------------------------------
Verifies M11-M22 compliance in analysis engines.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

try:
    from api.analysis_engine.stp_compute_resistance_rates import compute_resistance_metrics, aggregate_resistance_rates
    from api.analysis_engine.stp_temporal_aggregation import assert_no_future_leakage, flag_partial_windows
    from api.analysis_engine.stp_signal_validity import assess_signal_stability
    from api.analysis_engine.stp_antibiotic_pressure import compute_pressure_metrics
except ImportError:
    from analysis_engine.stp_compute_resistance_rates import compute_resistance_metrics, aggregate_resistance_rates
    from analysis_engine.stp_temporal_aggregation import assert_no_future_leakage, flag_partial_windows
    from analysis_engine.stp_signal_validity import assess_signal_stability
    from analysis_engine.stp_antibiotic_pressure import compute_pressure_metrics

# ==============================================================================
# M15, M21, M22: Resistance Rate Logic
# ==============================================================================

def test_resistance_rate_calculation_m15():
    """
    Verify M15: Rate = R / (S + I + R).
    Verify I is in denominator but NOT numerator.
    """
    # Create chunk with 10 S, 5 I, 5 R
    data = {
        'ast_result': ['S']*10 + ['I']*5 + ['R']*5
    }
    df = pd.DataFrame(data)
    
    result = compute_resistance_metrics(df, min_threshold=10)
    
    # Total = 20
    # R = 5
    # Expected Rate = 5/20 = 0.25
    
    assert result['tested_count'] == 20
    assert result['resistant_count'] == 5
    assert result['intermediate_count'] == 5
    assert result['resistance_rate'] == 0.25
    assert result['is_stable'] is True

def test_explicit_exclusion_of_na_m21():
    """
    Verify M21: NA/NaN values are strictly excluded from tested_count.
    """
    # 5 S, 5 R, 5 NA, 5 NaN
    data = {
        'ast_result': ['S']*5 + ['R']*5 + ['NA']*5 + [np.nan]*5
    }
    df = pd.DataFrame(data)
    
    result = compute_resistance_metrics(df, min_threshold=1)
    
    # Total valid = 10
    assert result['tested_count'] == 10
    assert result['susceptible_count'] == 5
    assert result['resistant_count'] == 5
    # 5/10 = 0.5
    assert result['resistance_rate'] == 0.5

def test_zero_and_low_denominator_handling_m22():
    """
    Verify M22: 
    - Count=0 -> Rate=None
    - Count<Threshold -> Rate=Calc, Stable=False, Reason=LOW_SAMPLE_SIZE
    """
    # Case 1: Zero Count
    df_empty = pd.DataFrame({'ast_result': [np.nan]})
    res_empty = compute_resistance_metrics(df_empty)
    assert res_empty['tested_count'] == 0
    assert res_empty['resistance_rate'] is None
    assert res_empty['is_stable'] is False
    assert res_empty['suppression_reason'] == 'NO_DATA'
    
    # Case 2: Low Count ( Threshold=30, N=10 )
    df_low = pd.DataFrame({'ast_result': ['S']*5 + ['R']*5}) # N=10
    res_low = compute_resistance_metrics(df_low, min_threshold=30)
    
    assert res_low['tested_count'] == 10
    assert res_low['resistance_rate'] == 0.5
    assert res_low['is_stable'] is False
    assert res_low['suppression_reason'] == 'LOW_SAMPLE_SIZE'


# ==============================================================================
# M13, M16: Temporal Logic
# ==============================================================================

def test_temporal_firewall_m13():
    """
    Verify M13: assert_no_future_leakage raises error for future data.
    """
    df = pd.DataFrame({'sample_date': pd.to_datetime(['2025-01-01', '2025-01-02'])})
    ref_date = pd.Timestamp('2025-01-01')
    
    with pytest.raises(ValueError, match="Temporal Leakage Detected"):
        assert_no_future_leakage(df, ref_date)

def test_partial_window_flagging_m16():
    """
    Verify M16: Partial windows are flagged correctly.
    """
    # Dataset coverage: Jan 1 to Jan 14.
    # Week 1: Jan 1 (Wed) -> Jan 7 (Tue). Partial? 
    #   If Window is Mon-Sun
    #   Let's assume our aggregator uses W-MON.
    
    dataset_start = pd.Timestamp('2025-01-01') # Wednesday
    dataset_end = pd.Timestamp('2025-01-31')   # Friday
    
    # Week starting Dec 30 (Mon). Overlap Jan 1-5 (5 days). Full is 7.
    # This should be partial.
    
    # Create aggregated DF
    df_agg = pd.DataFrame({
        'week_start': [pd.Timestamp('2024-12-30'), pd.Timestamp('2025-01-13')]
    })
    
    # 2024-12-30 ends 2025-01-05.
    # Dataset starts 2025-01-01.
    # Overlap: Jan 1 to Jan 5 = 5 days. Partial.
    
    # 2025-01-13 ends 2025-01-19.
    # Fully inside.
    
    res = flag_partial_windows(
        df_agg, 'week_start', 'W-MON', dataset_start, dataset_end
    )
    
    # Check Row 1 (Partial)
    assert res.iloc[0]['is_partial_window'] == True
    assert res.iloc[0]['coverage_days'] < 7
    
    # Check Row 2 (Full)
    assert res.iloc[1]['is_partial_window'] == False
    assert res.iloc[1]['coverage_days'] == 7


# ==============================================================================
# M17: Bias Logic
# ==============================================================================

def test_availability_bias_filter_m17():
    """
    Verify M17: Antibiotics with low coverage are excluded from Shannon Index.
    """
    # 1 Ward, 100 Isolates.
    # Abx A: Tested 100 times (100% coverage)
    # Abx B: Tested 100 times (100% coverage)
    # Abx C: Tested 5 times (5% coverage) -> Should be excluded if thr=20%
    
    # Create synthetic data
    # Isolate 1-100
    
    rows = []
    for i in range(100):
        # Isolate ID
        iso = f"iso_{i}"
        # A and B tested for everyone
        rows.append({'ward': 'W1', 'antibiotic': 'Abx_A', 'isolate_id': iso, 'ast_result': 'S'})
        rows.append({'ward': 'W1', 'antibiotic': 'Abx_B', 'isolate_id': iso, 'ast_result': 'S'})
        
        # C only for first 5
        if i < 5:
             rows.append({'ward': 'W1', 'antibiotic': 'Abx_C', 'isolate_id': iso, 'ast_result': 'S'})
             
    df = pd.DataFrame(rows)
    
    # Run with threshold 20%
    res = compute_pressure_metrics(df, group_cols=['ward'], min_coverage_threshold=0.20)
    
    # Check results
    assert len(res) == 1
    row = res.iloc[0]
    
    excluded = row['excluded_antibiotics']
    assert 'Abx_C' in excluded
    assert 'Abx_A' not in excluded
    
    # Shannon should be calc on A and B (50/50 split of counts)
    # 100 counts A, 100 counts B.
    # p = 0.5, 0.5
    # H = - (0.5 ln 0.5 + 0.5 ln 0.5) = - ( -0.346 + -0.346 ) = 0.693
    # If C included (counts 5): 100, 100, 5. Total 205.
    
    assert row['shannon_index'] > 0.6
