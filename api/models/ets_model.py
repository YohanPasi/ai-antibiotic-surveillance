"""
Exponential Smoothing (ETS) Model
Advanced statistical forecasting with automatic trend and seasonality detection
"""
import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import joblib
import os
import sys
import warnings
from typing import Tuple, Optional

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.base_model import BaseModel

warnings.filterwarnings('ignore')

class ETSModel(BaseModel):
    """
    Exponential Smoothing (Holt-Winters) model.
    Automatically detects optimal trend and seasonal components.
    """
    
    def __init__(self, 
                 trend: str = 'add',
                 seasonal: str = None,
                 seasonal_periods: int = None,
                 damped_trend: bool = False):
        """
        Initialize ETS model.
        
        Args:
            trend: Type of trend component ('add', 'mul', or None)
            seasonal: Type of seasonal component ('add', 'mul', or None)
            seasonal_periods: Number of periods in a season
            damped_trend: Use damped trend (default: False)
        """
        super().__init__(name='ETS')
        self.trend = trend
        self.seasonal = seasonal
        self.seasonal_periods = seasonal_periods
        self.damped_trend = damped_trend
        self.model = None
        self.fitted_model = None
        
        self.hyperparameters = {
            'trend': trend,
            'seasonal': seasonal,
            'seasonal_periods': seasonal_periods,
            'damped_trend': damped_trend
        }
        
    def fit(self, historical_data: pd.DataFrame) -> None:
        """
        Fit ETS model on historical data.
        
        Args:
            historical_data: DataFrame with 'susceptibility_percent' column
        """
        values = historical_data['susceptibility_percent'].dropna().values
        
        if len(values) < 4:
            raise ValueError("ETS requires at least 4 data points")
        
        # Auto-detect best configuration
        best_aic = np.inf
        best_config = None
        best_model = None
        
        # Try different configurations
        configs = [
            {'trend': 'add', 'seasonal': None, 'damped_trend': False},
            {'trend': 'add', 'seasonal': None, 'damped_trend': True},
            {'trend': None, 'seasonal': None, 'damped_trend': False},
        ]
        
        for config in configs:
            try:
                model = ExponentialSmoothing(
                    values,
                    trend=config['trend'],
                    seasonal=config['seasonal'],
                    seasonal_periods=config.get('seasonal_periods'),
                    damped_trend=config['damped_trend']
                )
                fitted = model.fit(optimized=True)
                
                if fitted.aic < best_aic:
                    best_aic = fitted.aic
                    best_config = config
                    best_model = fitted
            except:
                continue
        
        if best_model is None:
            # Simple exponential smoothing fallback
            model = ExponentialSmoothing(values, trend=None, seasonal=None)
            best_model = model.fit(optimized=True)
            best_config = {'trend': None, 'seasonal': None}
        
        self.fitted_model = best_model
        self.hyperparameters.update(best_config)
        self.is_trained = True
    
    def predict(self, steps: int = 1) -> Tuple[float, Optional[float], Optional[float]]:
        """
        Generate ETS forecast.
        
        Args:
            steps: Number of steps ahead to predict
            
        Returns:
            Tuple of (predicted_value, lower_bound, upper_bound)
        """
        if not self.is_trained:
            raise ValueError("Model must be fitted before prediction")
        
        # Generate forecast with confidence intervals
        forecast = self.fitted_model.forecast(steps=steps)
        prediction = float(forecast[-1])
        
        # Get prediction intervals (approximate using forecast variance)
        try:
            pred_int = self.fitted_model.get_prediction(start=len(self.fitted_model.fittedvalues), 
                                                        end=len(self.fitted_model.fittedvalues) + steps - 1)
            conf_int = pred_int.conf_int(alpha=0.05)
            lower_bound = float(conf_int.iloc[-1, 0])
            upper_bound = float(conf_int.iloc[-1, 1])
        except:
            # Fallback: use residual std
            std = np.std(self.fitted_model.resid)
            lower_bound = prediction - 1.96 * std
            upper_bound = prediction + 1.96 * std
        
        # Clamp to valid range
        prediction = np.clip(prediction, 0, 100)
        lower_bound = np.clip(lower_bound, 0, 100)
        upper_bound = np.clip(upper_bound, 0, 100)
        
        return prediction, lower_bound, upper_bound
    
    def save_model(self, filepath: str) -> None:
        """Save ETS model."""
        joblib.dump({
            'fitted_model': self.fitted_model,
            'hyperparameters': self.hyperparameters,
            'is_trained': self.is_trained
        }, filepath)
    
    def load_model(self, filepath: str) -> None:
        """Load ETS model."""
        data = joblib.load(filepath)
        self.fitted_model = data['fitted_model']
        self.hyperparameters = data['hyperparameters']
        self.is_trained = data['is_trained']
