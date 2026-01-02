"""
Simple Moving Average Model
Baseline model for time series forecasting
Uses weighted moving average with exponential decay for better recent-data weighting
"""
import numpy as np
import pandas as pd
import joblib
from typing import Tuple, Optional, Dict
import os
import sys

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.base_model import BaseModel

class SMAModel(BaseModel):
    """
    Enhanced Simple Moving Average model with exponential weighting.
    More recent observations get higher weights.
    """
    
    def __init__(self, window_size: int = 4, use_exponential: bool = True, alpha: float = 0.3):
        """
        Initialize SMA model.
        
        Args:
            window_size: Number of recent weeks to consider (default: 4)
            use_exponential: Use exponential weighting (default: True)
            alpha: Smoothing factor for exponential weighting (0-1, default: 0.3)
        """
        super().__init__(name='SMA')
        self.window_size = window_size
        self.use_exponential = use_exponential
        self.alpha = alpha
        self.historical_values = None
        self.hyperparameters = {
            'window_size': window_size,
            'use_exponential': use_exponential,
            'alpha': alpha
        }
        
    def fit(self, historical_data: pd.DataFrame) -> None:
        """
        Fit the SMA model (stores historical data).
        
        Args:
            historical_data: DataFrame with 'susceptibility_percent' column
        """
        # Extract susceptibility percentages, drop NaN
        self.historical_values = historical_data['susceptibility_percent'].dropna().values
        
        if len(self.historical_values) == 0:
            raise ValueError("No valid historical data to fit")
        
        self.is_trained = True
        
    def predict(self, steps: int = 1) -> Tuple[float, Optional[float], Optional[float]]:
        """
        Predict next week's S% using weighted moving average.
        
        Args:
            steps: Number of steps ahead (always 1 for SMA)
            
        Returns:
            Tuple of (predicted_value, lower_bound, upper_bound)
        """
        if not self.is_trained:
            raise ValueError("Model must be fitted before prediction")
        
        # Take most recent window_size values
        recent_values = self.historical_values[-self.window_size:]
        
        if len(recent_values) == 0:
            # Fallback to overall mean
            prediction = np.mean(self.historical_values)
        elif self.use_exponential:
            # Exponential weighted moving average
            weights = np.array([self.alpha * (1 - self.alpha) ** i for i in range(len(recent_values))][::-1])
            weights = weights / weights.sum()  # Normalize
            prediction = np.average(recent_values, weights=weights)
        else:
            # Simple average
            prediction = np.mean(recent_values)
        
        # Calculate confidence interval based on recent volatility
        if len(self.historical_values) >= 3:
            recent_std = np.std(self.historical_values[-self.window_size:])
            lower_bound = max(0, prediction - 1.96 * recent_std)  # 95% CI
            upper_bound = min(100, prediction + 1.96 * recent_std)
        else:
            lower_bound = None
            upper_bound = None
        
        return prediction, lower_bound, upper_bound
    
    def save_model(self, filepath: str) -> None:
        """Save model to disk."""
        joblib.dump({
            'historical_values': self.historical_values,
            'hyperparameters': self.hyperparameters,
            'is_trained': self.is_trained
        }, filepath)
    
    def load_model(self, filepath: str) -> None:
        """Load model from disk."""
        data = joblib.load(filepath)
        self.historical_values = data['historical_values']
        self.hyperparameters = data['hyperparameters']
        self.is_trained = data['is_trained']
        
        # Restore hyperparameters
        self.window_size = self.hyperparameters.get('window_size', 4)
        self.use_exponential = self.hyperparameters.get('use_exponential', True)
        self.alpha = self.hyperparameters.get('alpha', 0.3)
