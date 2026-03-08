
"""
STP Stage 4: Validation Tests
-----------------------------
Verifies M41-M55 Governance Logic: Metrics, Calibration Impact, Stability, Cost.
"""

import sys
import os
import pytest
import pandas as pd
import numpy as np

# Path setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Engines
from api.evaluation_engine.stp_metrics import compute_priority_metrics, compute_clinical_cost_score
from api.evaluation_engine.stp_calibration import compute_calibration_curve_data
from api.evaluation_engine.stp_calibration_impact import assess_calibration_impact
from api.evaluation_engine.stp_shap_stability import assess_explanation_stability
from api.evaluation_engine.stp_ward_stratified_eval import compute_stratified_metrics

# 1. Metric Priorities (M44) & Cost (M53)
def test_metric_priorities_m44_m53():
    # Scenario: High False Negatives (Dangerous)
    y_true = np.array([1, 1, 1, 0, 0])
    y_prob = np.array([0.1, 0.2, 0.9, 0.1, 0.1]) # 2 Misses, 1 Hit
    
    metrics = compute_priority_metrics(y_true, y_prob, threshold=0.5)
    
    # Check Math
    # TP=1, FN=2, TN=2, FP=0
    assert metrics['TP'] == 1
    assert metrics['FN'] == 2
    
    # M44: NPV = TN / (TN+FN) = 2/(2+2) = 0.5
    assert metrics['NPV'] == 0.5
    
    # M53: Clinical Cost
    # Normalized Cost = ((FN*10 + FP*1) / Total) * 100
    # Cost = ((2*10 + 0) / 5) * 100 = (20/5)*100 = 400.0
    cost = compute_clinical_cost_score(metrics)
    assert cost == 400.0

# 2. Calibration Impact (M52)
def test_calibration_impact_m52():
    y_true = np.array([1, 1, 0, 0])
    
    # Raw: Poorly calibrated (confident wrongs)
    y_raw = np.array([0.4, 0.4, 0.6, 0.6]) 
    
    # Calibrated: Better
    y_cal = np.array([0.8, 0.8, 0.2, 0.2])
    
    impact = assess_calibration_impact(pd.Series(y_true), pd.Series(y_raw), pd.Series(y_cal))
    
    # Brier should improve (decrease)
    # Raw Brier: ((1-0.4)^2 + (1-0.4)^2 + (0-0.6)^2 + (0-0.6)^2)/4 = (0.36*4)/4 = 0.36
    # Cal Brier: ((1-0.8)^2 + (1-0.8)^2 + (0-0.2)^2 + (0-0.2)^2)/4 = (0.04*4)/4 = 0.04
    # Delta = 0.04 - 0.36 = -0.32
    
    assert impact['impact']['calibration_beneficial'] is True
    assert impact['impact']['delta_brier'] < 0

# 3. SHAP Stability (M54)
def test_shap_stability_m54():
    t1_feats = ['age', 'ward', 'abx_history']
    t2_feats = ['age', 'ward', 'comorbidity'] # 2 overlap, 1 diff
    
    stats = assess_explanation_stability(t2_feats, t1_feats)
    
    # Intersection = 2 (age, ward)
    # Union = 4 (age, ward, abx_history, comorbidity)
    # Jaccard = 2/4 = 0.5
    print(f"DEBUG: Jaccard Index = {stats['jaccard_index']}")
    assert stats['jaccard_index'] == pytest.approx(0.5)
    assert 'age' in stats['stable_features']
    assert 'abx_history' in stats['dropped_features']

# 4. Ward Stratification (M45)
def test_ward_stratification_m45():
    df = pd.DataFrame({
        'ward': ['ICU A', 'ICU B', 'Gen Ward'],
        'y_true': [1, 0, 1],
        'y_prob': [0.9, 0.1, 0.8]
    })
    
    # Should infer ICU/Non-ICU metrics
    results = compute_stratified_metrics(df)
    
    assert 'ALL' in results
    assert 'ICU' in results 
    # 'NON_ICU' key based on logic: Gen Ward doesn't have "ICU" in name -> NON_ICU
    assert 'NON_ICU' in results
    
    # ICU Subset: Rows 0 and 1. (1, 0.9) -> TP, (0, 0.1) -> TN. Perfect.
    assert results['ICU']['Sensitivity'] == 1.0
