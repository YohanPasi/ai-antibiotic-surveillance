
"""
STP Stage 5: Ops Validation Tests
---------------------------------
Verifies M58-M75 Governance Logic: Alerting, Drift, Governance.
"""

import sys
import os
import pytest
import numpy as np
from datetime import datetime, timedelta

# Path setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Engines
from api.ops_engine.stp_alert_manager import AlertManager
from api.ops_engine.stp_drift_monitor import calculate_psi, check_for_drift
from api.ops_engine.stp_model_governance import GovernanceController

# 1. Alert Fatigue (M60)
def test_alert_fatigue_m60():
    manager = AlertManager()
    
    # History has a critical alert from 1 hour ago
    history = [{
        'timestamp': datetime.now() - timedelta(hours=1),
        'severity': 'critical'
    }]
    
    # Try to fire same alert
    suppress, reason = manager.should_suppress_alert("target_1", "critical", history)
    
    assert suppress is True
    assert "Deduplicated" in reason
    
    # Try different severity
    suppress2, _ = manager.should_suppress_alert("target_1", "warning", history)
    assert suppress2 is False

# 2. Drift Detection & Incidents (M58, M72)
def test_drift_detection_m58_m72():
    # No Drift
    expected = np.random.normal(0.5, 0.1, 1000)
    actual = np.random.normal(0.5, 0.1, 1000)
    
    result = check_for_drift(expected, actual)
    assert result['status'] == "OK"
    assert result['incident_event'] is None
    
    # Critical Drift
    actual_drift = np.random.normal(0.8, 0.1, 1000) # Shifted mean
    
    result_drift = check_for_drift(expected, actual_drift)
    # PSI should be high
    assert result_drift['psi'] > 0.2
    assert result_drift['status'] == "CRITICAL_DRIFT"
    assert result_drift['incident_event'] is not None
    assert result_drift['incident_event']['type'] == "DRIFT" # M72

# 3. Governance Kill Switch (M63)
def test_kill_switch_m63():
    gov = GovernanceController()
    
    # Mock
    result = gov.deactivate_model(
        model_id="uuid-test",
        reason="Test Kill Switch",
        approved_by="Admin"
    )
    
    assert result is True
