"""
Facebook Prophet Model
Advanced time series forecasting with trend, seasonality, and uncertainty intervals
Optimized for sparse medical data with automatic handling of missing values
"""
import numpy as np
import pandas as pd
from prophet import Prophet
import joblib
from typing import Tuple, Optional
import os
import sys
import warnings

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.base_model import BaseModel

warnings.filterwarnings('ignore')

class ProphetModel(BaseModel):
    """
    Facebook Prophet model for robust time series forecasting.
    Handles missing data, uncertainty quantification, and seasonal patterns.
    """
    
    def __init__(self, 
                 changepoint_prior_scale: float = 0.05,
                 seasonality_prior_scale: float = 0.1,
                 interval_width: float = 0.95,
                 yearly_seasonality: bool = False,
                 weekly_seasonality: bool = False,
                 daily_seasonality: bool = False):
        """
        Initialize Prophet model with medical data-optimized parameters.
        
        Args:
            changepoint_prior_scale: Flexibility of trend (lower = more stable, default: 0.05)
            seasonality_prior_scale: Strength of seasonality (default: 0.1)
            interval_width: Width of uncertainty intervals (default: 0.95 for 95% CI)
            yearly_seasonality: Enable yearly seasonality (default: False - not enough data)
            weekly_seasonality: Enable weekly patterns (default: False)
            daily_seasonality: Enable daily patterns (default: False - weekly data)
        """
        super().__init__(name='Prophet')
        self.changepoint_prior_scale = changepoint_prior_scale
        self.seasonality_prior_scale = seasonality_prior_scale
        self.interval_width = interval_width
        
        # Initialize Prophet model
        self.model = Prophet(
            changepoint_prior_scale=changepoint_prior_scale,
            seasonality_prior_scale=seasonality_prior_scale,
            interval_width=interval_width,
            yearly_seasonality=yearly_seasonality,
            weekly_seasonality=weekly_seasonality,
            daily_seasonality=daily_seasonality,
            uncertainty_samples=1000  # High precision for uncertainty
        )
        
        self.hyperparameters = {
            'changepoint_prior_scale': changepoint_prior_scale,
            'seasonality_prior_scale': seasonality_prior_scale,
            'interval_width': interval_width
        }
        
        self.forecast = None
        
    def fit(self, historical_data: pd.DataFrame) -> None:
        """
        Fit Prophet model on historical data.
        
        Args:
            historical_data: DataFrame with 'week_start_date' and 'susceptibility_percent'
        """
        # Prepare data in Prophet format (ds, y)
        prophet_df = pd.DataFrame({
            'ds': pd.to_datetime(historical_data['week_start_date']),
            'y': historical_data['susceptibility_percent']
        })
        
        # Remove rows with NaN values in y
        prophet_df = prophet_df.dropna(subset=['y'])
        
        if len(prophet_df) < 2:
            raise ValueError("Prophet requires at least 2 non-null data points")
        
        # Fit model
        self.model.fit(prophet_df)
        self.is_trained = True
        
    def predict(self, steps: int = 1) -> Tuple[float, Optional[float], Optional[float]]:
        """
        Generate prediction with uncertainty intervals.
        
        Args:
            steps: Number of weeks ahead to predict (default: 1)
            
        Returns:
            Tuple of (predicted_value, lower_bound, upper_bound)
        """
        if not self.is_trained:
            raise ValueError("Model must be fitted before prediction")
        
        # Create future dataframe
        future = self.model.make_future_dataframe(periods=steps, freq='W')
        
        # Generate forecast
        self.forecast = self.model.predict(future)
        
        # Get the last prediction (next week)
        last_forecast = self.forecast.iloc[-1]
        
        prediction = float(last_forecast['yhat'])
        lower_bound = float(last_forecast['yhat_lower'])
        upper_bound = float(last_forecast['yhat_upper'])
        
        # Clamp to valid percentage range
        prediction = np.clip(prediction, 0, 100)
        lower_bound = np.clip(lower_bound, 0, 100)
        upper_bound = np.clip(upper_bound, 0, 100)
        
        return prediction, lower_bound, upper_bound
    
    def save_model(self, filepath: str) -> None:
        """Save Prophet model to disk."""
        joblib.dump({
            'model': self.model,
            'hyperparameters': self.hyperparameters,
            'is_trained': self.is_trained
        }, filepath)
    
    def load_model(self, filepath: str) -> None:
        """Load Prophet model from disk."""
        data = joblib.load(filepath)
        self.model = data['model']
        self.hyperparameters = data['hyperparameters']
        self.is_trained = data['is_trained']
        
        # Restore hyperparameters
        self.changepoint_prior_scale = self.hyperparameters.get('changepoint_prior_scale', 0.05)
        self.seasonality_prior_scale = self.hyperparameters.get('seasonality_prior_scale', 0.1)
        self.interval_width = self.hyperparameters.get('interval_width', 0.95)
