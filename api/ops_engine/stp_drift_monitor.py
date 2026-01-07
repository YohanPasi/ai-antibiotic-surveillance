
"""
STP Stage 5: Drift Monitor
--------------------------
Detects data and prediction drift using statistical tests.
ENFORCES M58: Feature PSI (Population Stability Index).
ENFORCES M59: Prediction Shift.
ENFORCES M72: Incident Escalation on Critical Drift.
"""

import numpy as np
import logging

logger = logging.getLogger(__name__)

def calculate_psi(expected_array, actual_array, buckets=10):
    """
    Computes Population Stability Index (PSI).
    PSI < 0.1: No Drift
    PSI 0.1 - 0.2: Moderate
    PSI > 0.2: Significant (Critical)
    """
    def scale_range(input, min, max):
        input += (1e-6) # Avoid zero division
        input /= (1.002) # Scale to slightly less than 1
        return input

    # Simple binning strategy for prototype
    breakpoints = np.linspace(0, 1, buckets + 1)
    
    # Bucket counts
    expected_percents = np.histogram(expected_array, breakpoints)[0] / len(expected_array)
    actual_percents = np.histogram(actual_array, breakpoints)[0] / len(actual_array)
    
    # PSI calculation
    def sub_psi(e_perc, a_perc):
        if a_perc == 0: a_perc = 0.0001
        if e_perc == 0: e_perc = 0.0001
        
        value = (e_perc - a_perc) * np.log(e_perc / a_perc)
        return value

    psi_values = [sub_psi(expected_percents[i], actual_percents[i]) for i in range(buckets)]
    return sum(psi_values)

def check_for_drift(historical_probs, current_probs):
    """
    Run PSI check and determine if Incident needs escalation (M72).
    """
    psi_score = calculate_psi(historical_probs, current_probs)
    
    status = "OK"
    severity = "LOW"
    incident = None
    
    if psi_score > 0.2:
        status = "CRITICAL_DRIFT"
        severity = "HIGH"
        # M72: Incident
        incident = {
            "type": "DRIFT",
            "severity": "HIGH",
            "description": f"PSI Score {psi_score:.2f} exceeds 0.2 threshold.",
            "triggered_by": "stp_drift_monitor"
        }
    elif psi_score > 0.1:
        status = "WARNING"
        severity = "MED"
        
    logger.info(f"Drift Check: PSI={psi_score:.3f} | Status={status}")
    
    return {
        "psi": psi_score,
        "status": status,
        "incident_event": incident
    }
