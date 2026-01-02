"""
Prediction Service - Core Logic
Handles model loading and prediction generation
"""
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple, List
import logging
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path to ensure models can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import model classes so joblib can find them during deserialization
from models.sma_model import SMAModel
from models.arima_model import ARIMAModel
from models.ets_model import ETSModel
from models.lstm_model import LSTMModel
import torch
import torch.nn as nn

logger = logging.getLogger(__name__)

class PredictionService:
    """Service for generating AST predictions using trained models."""
    
    @staticmethod
    def load_best_model(model_path: str):
        """Load a trained model from disk."""
        try:
            model_data = joblib.load(model_path)
            return model_data
        except Exception as e:
            logger.error(f"Failed to load model {model_path}: {e}")
            return None
    
    @staticmethod
    def get_alert_level(s_percentage: float) -> str:
        """Determine alert level based on S%."""
        if s_percentage >= 80:
            return "green"
        elif s_percentage >= 60:
            return "amber"
        else:
            return "red"

    @staticmethod
    def generate_stewardship_prompt(alert_level: str, organism: str, antibiotic: str, ward: Optional[str] = None) -> str:
        """Generate actionable stewardship advice based on alert level."""
        loc = f"in {ward}" if ward else "unit-wide"
        
        if alert_level == "green":
            return f"Susceptibility is stable. {antibiotic} remains a viable empiric option for {organism} {loc}."
        elif alert_level == "amber":
            return f"⚠️ Early Warning: Susceptibility to {antibiotic} is declining {loc}. Review recent cases and consider targeted cultures."
        else: # red
            return f"🚨 CRITICAL: {antibiotic} susceptibility is compromised (<60%) {loc}. Avoid as empiric monotherapy for {organism}. Audit infection controls."
    
    @staticmethod
    def load_lstm_model(model_path: str):
        """Load the PyTorch LSTM model."""
        try:
            model = LSTMModel()
            # map_location='cpu' is crucial if trained on GPU but running on CPU
            model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
            model.eval()
            return model
        except Exception as e:
            logger.error(f"Failed to load LSTM model {model_path}: {e}")
            return None

    @staticmethod
    def get_recent_history(cursor, ward, organism, antibiotic, current_week_date) -> List[float]:
        """
        Fetch the last 4 weeks of Observed S% history for LSTM input.
        Returns list of floats [week-4, week-3, week-2, week-1].
        """
        try:
            # Query for history BEFORE the current prediction week
            cursor.execute("""
                SELECT susceptibility_percent 
                FROM ast_weekly_aggregated
                WHERE ward = %s AND organism = %s AND antibiotic = %s 
                  AND week_start_date < %s
                ORDER BY week_start_date DESC
                LIMIT 4
            """, (ward, organism, antibiotic, current_week_date))
            
            rows = cursor.fetchall()
            
            # If no history, return empty
            if not rows: return []
            
            # Extract and Reverse to be Chronological (Oldest -> Newest)
            history = [float(r[0]) for r in rows]
            history.reverse()
            
            return history
        except Exception as e:
            logger.error(f"Error fetching history for {ward}/{organism}: {e}")
            return []

    @staticmethod
    def predict_with_lstm(model: LSTMModel, recent_history: list) -> float:
        """
        Run LSTM inference on a sequence of the last 4 float values (0.0-1.0 or 0-100).
        Expects input 0-100 scale, normalizes to 0-1 internally, returns 0-100.
        """
        if len(recent_history) < 4:
            # Need 4 weeks of context. Padding if necessary (e.g. repeat last value)
            if not recent_history: return 75.0 # Fallback
            while len(recent_history) < 4:
                recent_history.insert(0, recent_history[0])
        
        # Take last 4
        seq = recent_history[-4:]
        
        # Normalize 0-100 -> 0-1
        seq_norm = [x / 100.0 for x in seq]
        
        # Prepare Tensor (Batch=1, Seq=4, Feature=1)
        input_tensor = torch.FloatTensor(seq_norm).view(1, 4, 1)
        
        with torch.no_grad():
            output = model(input_tensor)
            
        # Denormalize 0-1 -> 0-100
        prediction_raw = output.item()
        prediction_pct = prediction_raw * 100.0
        
        return float(np.clip(prediction_pct, 0.0, 100.0))

    @staticmethod
    def get_hybrid_status(observed_s: float, baseline_lower: float, lstm_forecast: float, previous_statuses: List[str] = []) -> Tuple[str, str, str]:
        """
        Implements the CONSENSUS LOGIC V2 (Hybrid + Persistence).
        Returns: (Status, Direction, Reason)
        """
        # 1. Base Hybrid Logic (Snapshot)
        status = "green"
        reason = "Stable"
        
        stat_breach = observed_s < baseline_lower
        forecast_breach = lstm_forecast < baseline_lower
        declining = lstm_forecast < (observed_s - 5.0) 
        
        if stat_breach:
            status = "red"
            reason = "Statistical Breach (Observed < Baseline)"
        elif forecast_breach and declining:
            status = "red"
            reason = "Proactive Alert (Forecasted Breach + Decline)"
        elif declining or forecast_breach:
            status = "amber"
            reason = "Early Warning (Declining Trend or Forecast Risk)"
        else:
            status = "green"
            reason = "Stable within Baseline"
            
        # 2. Persistence Logic (Temporal Memory)
        # previous_statuses is assumed ordered Recent -> Past (e.g. [LastWeek, 2WeeksAgo, ...])
        
        if status == "amber":
            # Rule: Two consecutive Amber -> Amber-High (Escalated Watch)
            if previous_statuses and previous_statuses[0] in ["amber", "amber-high"]:
                status = "amber-high"
                reason = "Escalation: Sustained Amber (2+ Weeks)"
                
        if status == "red":
            # Rule: Red followed by Red + Forecast Decline -> Critical
            if previous_statuses and previous_statuses[0] == "red" and declining:
                status = "critical" 
                reason = "CRITICAL: Persistent Erosion + Declining Forecast"
            # Rule: Two Red in three weeks -> Confirmed
            elif len(previous_statuses) >= 2 and (previous_statuses[0] == "red" or previous_statuses[1] == "red"):
                reason = "Confirmed Resistance Erosion (Multi-week Red)"

        # 3. Direction
        direction = "Stable"
        if declining:
            direction = "Declining"
        elif lstm_forecast > (observed_s + 5.0):
            direction = "Improving"
            
        return status, direction, reason

    @staticmethod
    def generate_detailed_stewardship(status: str, organism: str, antibiotic: str, ward: str) -> Tuple[str, str]:
        """
        Generates Context-Aware Stewardship Prompt & Domain.
        Returns: (Prompt, Domain)
        """
        prompt = ""
        domain = "General Surveillance"
        
        # Normalize inputs
        org_norm = organism.lower()
        abx_norm = antibiotic.lower()
        
        # Domain Mapping
        if "pseudomonas" in org_norm:
            if "meropenem" in abx_norm or "carbapenem" in abx_norm:
                domain = "Empiric Review + Environmental Audit"
            else:
                domain = "Device Care + Culture Review"
        elif "acinetobacter" in org_norm:
            domain = "Infection Control + Cohorting"
        
        # Status-Based Logic
        if status == "green":
            prompt = f"Susceptibility is within expected limits. Continue standard surveillance."
            domain = "Routine Monitoring"
            
        elif status in ["amber", "amber-high"]:
            if "amber-high" in status:
                prompt = f"⚠️ ESCALATION: Sustained instability detected for {organism}. Review recent empiric use of {antibiotic} in {ward}."
            else:
                prompt = f"⚠️ Early Warning: Susceptibility showing signs of decline. Monitor new cultures closely."
                
        elif status in ["red", "critical"]:
            if "critical" in status:
                 prompt = f"🚨 CRITICAL SIGNAL: Persistent and deepening resistance erosion. Immediate stewardship intervention required for {ward}."
                 domain = "URGENT INTERVENTION"
            else:
                 prompt = f"🛑 BREACH: Susceptibility has fallen below statistical baseline. Restrict empiric {antibiotic} verify recent isolates."
        
        return prompt, domain

    @staticmethod
    def generate_demo_prediction(organism: str, antibiotic: str) -> Dict:
        """
        Generate a demo prediction when no trained model is available.
        Uses simple statistical rules based on typical AST patterns.
        """
        # Demo predictions based on organism-antibiotic pairs
        base_s_percent = 75.0  # Default baseline
        
        # Adjust based on organism
        if "Pseudomonas" in organism:
            base_s_percent = 70.0  # Generally more resistant
        elif "Acinetobacter" in organism:
            base_s_percent = 65.0  # Often highly resistant
        elif "E. coli" in organism or "Escherichia" in organism:
            base_s_percent = 80.0  # Generally more susceptible
        
        # Add some randomness for demonstration
        import random
        random.seed(hash(organism + antibiotic) % 1000)
        
        variation = random.uniform(-10, 10)
        prediction = np.clip(base_s_percent + variation, 30, 95)
        
        lower_bound = np.clip(prediction - 8, 20, 100)
        upper_bound = np.clip(prediction + 8, 20, 100)
        
        alert = PredictionService.get_alert_level(prediction)
        
        return {
            "prediction": round(prediction, 2),
            "lower_bound": round(lower_bound, 2),
            "upper_bound": round(upper_bound, 2),
            "alert_level": alert,
            "model_used": "Demo (No trained model)",
            "mae_score": None,
            "confidence": "Low - Demo mode"
        }
