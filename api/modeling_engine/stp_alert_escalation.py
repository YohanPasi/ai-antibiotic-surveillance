
"""
STP Stage 3: Alert Escalation (M34)
----------------------------------
Governance logic for converting raw signals into actionable Alerts.
ENFORCES M34: Signals must meet severity/persistence criteria.
"""

from typing import Dict, Any

def determine_risk_level(
    predicted_prob: float, 
    lower_ci: float,
    threshold: float,
    signal_strength: float = 0.0,
    is_stable: bool = True
) -> str:
    """
    Determines Risk Level (LOW, MEDIUM, HIGH) based on M34 rules.
    
    Rules:
    - HIGH:
        - Prob > Threshold AND Lower CI > Threshold (Confidence is high)
        - OR CUSUM Signal Strength > 5.0 (Strong statistical shift)
    - MEDIUM:
        - Prob > Threshold but Lower CI < Threshold (Unsure)
        - OR CUSUM Signal Strength > 4.0
    - LOW:
        - Prob < Threshold
        - OR Unstable signal
    """
    
    if not is_stable:
        return 'LOW' # M22/M34: Don't alert on unstable data
        
    # ML Forecast Logic
    ml_high = (predicted_prob > threshold) and (lower_ci > threshold)
    ml_med = (predicted_prob > threshold)
    
    # Statistical Signal Logic (CUSUM)
    stats_high = (signal_strength > 5.0)
    stats_med = (signal_strength > 4.0)
    
    if ml_high or stats_high:
        return 'HIGH'
        
    if ml_med or stats_med:
        return 'MEDIUM'
        
    return 'LOW'
