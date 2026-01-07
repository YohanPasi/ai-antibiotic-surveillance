
import sys
import os
import pandas as pd
import numpy as np

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from api.analysis_engine.stp_compute_resistance_rates import compute_resistance_metrics
except ImportError:
    try:
        from analysis_engine.stp_compute_resistance_rates import compute_resistance_metrics
    except ImportError:
        # Fallback: assume running from root and api is package
        sys.path.append(os.getcwd())
        from api.analysis_engine.stp_compute_resistance_rates import compute_resistance_metrics

print("Imports successful.")

def test_m15_m21_m22():
    print("Testing M15, M21, M22 Logic...")
    
    # 1. M15: Rate Calculation & M21: NA Exclusion
    # 10 S, 5 I, 5 R, 5 NA
    df = pd.DataFrame({
        'ast_result': ['S']*10 + ['I']*5 + ['R']*5 + ['NA']*5
    })
    
    res = compute_resistance_metrics(df, min_threshold=10)
    
    # Validation M21
    if res['tested_count'] != 20:
        print(f"FAILED M21: tested_count {res['tested_count']} != 20")
        sys.exit(1)
        
    # Validation M15
    if res['resistant_count'] != 5:
        print(f"FAILED M15: resistant_count {res['resistant_count']} != 5")
        sys.exit(1)
    
    expected_rate = 5.0 / 20.0 # 0.25
    if res['resistance_rate'] != 0.25:
        print(f"FAILED M15: Rate {res['resistance_rate']} != 0.25")
        sys.exit(1)
        
    print("M15 & M21: PASSED")
    
    # 2. M22: Zero/Suppression
    # Zero count
    res_zero = compute_resistance_metrics(pd.DataFrame({'ast_result': ['NA']}))
    if res_zero['resistance_rate'] is not None:
         print(f"FAILED M22 (Zero): Rate {res_zero['resistance_rate']} is not None")
         sys.exit(1)
         
    # Low count
    res_low = compute_resistance_metrics(pd.DataFrame({'ast_result': ['S']*2}), min_threshold=10)
    if res_low['is_stable'] is not False:
        print(f"FAILED M22 (Low): is_stable is True")
        sys.exit(1)
    if res_low['suppression_reason'] != 'LOW_SAMPLE_SIZE':
        print(f"FAILED M22 (Low): Suppression reason mismatch")
        sys.exit(1)
        
    print("M22: PASSED")

if __name__ == "__main__":
    try:
        test_m15_m21_m22()
        print("ALL CHECKS PASSED")
        sys.exit(0)
    except Exception as e:
        print(f"CRITICAL FAILURE: {e}")
        sys.exit(1)
