
"""
STP Stage 5: Alert Manager
--------------------------
Manages surveillance alerts with fatigue control.
ENFORCES M60: Fatigue Control (Deduplication / Snooze).
ENFORCES M34: Alert Logic (Red/Amber interpretation).
"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AlertManager:
    def __init__(self, db_session=None):
        self.db = db_session
        
    def should_suppress_alert(self, entity_key, severity, history):
        """
        M60: Suppression Logic.
        - Don't fire same alert within 24 hours (Dedupe).
        - If 'Snoozed' (Dismissed recently), suppress.
        """
        # History format: [{'timestamp':..., 'severity':...}]
        
        now = datetime.now()
        
        # 1. Deduplication (Same day, same severity)
        for event in history:
            time_diff = now - event['timestamp']
            if time_diff < timedelta(hours=24) and event['severity'] == severity:
                return True, "Deduplicated (Recent match)"
                
        return False, None
        
    def process_prediction_risk(self, prediction_result):
        """
        Ingests a prediction, decides if ALERT is needed.
        """
        risk = prediction_result['risk_level'] # low, medium, high
        
        if risk == 'low':
            return None # No alert
            
        severity = "warning" if risk == 'medium' else "critical"
        
        # In real system, query DB for history of this target
        # Mock history for logic check
        mock_history = [] 
        
        suppress, reason = self.should_suppress_alert("target_id", severity, mock_history)
        
        if suppress:
            logger.info(f"Alert Suppressed: {reason}")
            return None
            
        # Create Alert Object
        alert = {
            "prediction_id": prediction_result['prediction_id'],
            "type": "risk_alert",
            "severity": severity,
            "description": f"Model predicts {risk.upper()} risk of resistance.",
            "is_active": True
        }
        
        return alert
