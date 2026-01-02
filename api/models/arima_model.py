"""
ARIMA/SARIMA Model
Statistical time series forecasting with auto-order selection
Optimized for sparse medical surveillance data
"""
import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import adfuller
import joblib
import os
import sys
import warnings
from typing import Tuple, Optional

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.base_model import BaseModel

warnings.filterwarnings('ignore')

class ARIMAModel(BaseModel):
    """
    ARIMA/SARIMA model with automatic order selection.
    Uses AIC criterion for optimal parameter selection.
    """
    
    def __init__(self, 
                 order: Tuple[int, int, int] = None,
                 seasonal_order: Tuple[int, int, int, int] = None,
                 auto_order: bool = True):
        """
        Initialize ARIMA model.
        
        Args:
            order: (p, d, q) for ARIMA. If None, will auto-select
            seasonal_order: (P, D, Q, s) for SARIMA. If None, no seasonality
            auto_order: Automatically select best order based on AIC (default: True)
        """
        super().__init__(name='ARIMA')
        self.order = order
        self.seasonal_order = seasonal_order
        self.auto_order = auto_order
        self.model = None
        self.fitted_model = None
        
        self.hyperparameters = {
            'order': order,
            'seasonal_order': seasonal_order,
            'auto_order': auto_order
        }
        
    def _check_stationarity(self, data: np.ndarray) -> int:
        """
        Check if time series is stationary using Augmented Dickey-Fuller test.
        Returns suggested differencing order.
        """
        if len(data) < 3:
            return 0
        
        try:
            result = adfuller(data)
            p_value = result[1]
            
            # If p-value > 0.05, series is non-stationary, need differencing
            if p_value > 0.05:
                return 1
            else:
                return 0
        except:
            return 0
    
    def _auto_select_order(self, data: np.ndarray) -> Tuple[int, int, int]:
        """
        Automatically select best ARIMA order using grid search with AIC.
        Limited search space for sparse data.
        """
        best_aic = np.inf
        best_order = (1, 0, 1)
        
        # Determine differencing order
        d = self._check_stationarity(data)
        
        # Grid search over limited p and q values (sparse data)
        p_range = range(0, min(3, len(data) // 2))
        q_range = range(0, min(3, len(data) // 2))
        
        for p in p_range:
            for q in q_range:
                try:
                    model = SARIMAX(data, order=(p, d, q), enforce_stationarity=False, enforce_invertibility=False)
                    fitted = model.fit(disp=False, maxiter=50)
                    
                    if fitted.aic < best_aic:
                        best_aic = fitted.aic
                        best_order = (p, d, q)
                except:
                    continue
        
        return best_order
    
    def fit(self, historical_data: pd.DataFrame) -> None:
        """
        Fit ARIMA model on historical data.
        
        Args:
            historical_data: DataFrame with 'susceptibility_percent' column
        """
        # Extract values, drop NaN
        values = historical_data['susceptibility_percent'].dropna().values
        
        if len(values) < 3:
            raise ValueError("ARIMA requires at least 3 data points")
        
        # Auto-select order if needed
        if self.auto_order or self.order is None:
            self.order = self._auto_select_order(values)
            self.hyperparameters['order'] = self.order
        
        # Fit SARIMAX model
        try:
            self.model = SARIMAX(
                values,
                order=self.order,
                seasonal_order=self.seasonal_order if self.seasonal_order else (0, 0, 0, 0),
                enforce_stationarity=False,
                enforce_invertibility=False
            )
            
            self.fitted_model = self.model.fit(disp=False, maxiter=100)
            self.is_trained = True
            
        except Exception as e:
            # Fallback to simpler model
            self.order = (1, 0, 1)
            self.model = SARIMAX(
                values,
                order=self.order,
                enforce_stationarity=False,
                enforce_invertibility=False
            )
            self.fitted_model = self.model.fit(disp=False, maxiter=50)
            self.is_trained = True
    
    def predict(self, steps: int = 1) -> Tuple[float, Optional[float], Optional[float]]:
        """
        Generate ARIMA forecast with confidence intervals.
        
        Args:
            steps: Number of weeks ahead to predict (default: 1)
            
        Returns:
            Tuple of (predicted_value, lower_bound, upper_bound)
        """
        if not self.is_trained:
            raise ValueError("Model must be fitted before prediction")
        
        # Generate forecast
        forecast_result = self.fitted_model.get_forecast(steps=steps)
        
        # Get prediction and confidence interval
        prediction = float(forecast_result.predicted_mean.iloc[-1])
        conf_int = forecast_result.conf_int(alpha=0.05)  # 95% CI
        
        lower_bound = float(conf_int.iloc[-1, 0])
        upper_bound = float(conf_int.iloc[-1, 1])
        
        # Clamp to valid percentage range
        prediction = np.clip(prediction, 0, 100)
        lower_bound = np.clip(lower_bound, 0, 100)
        upper_bound = np.clip(upper_bound, 0, 100)
        
        return prediction, lower_bound, upper_bound
    
    def save_model(self, filepath: str) -> None:
        """Save ARIMA model to disk."""
        joblib.dump({
            'fitted_model': self.fitted_model,
            'order': self.order,
            'seasonal_order': self.seasonal_order,
            'hyperparameters': self.hyperparameters,
            'is_trained': self.is_trained
        }, filepath)
    
    def load_model(self, filepath: str) -> None:
        """Load ARIMA model from disk."""
        data = joblib.load(filepath)
        self.fitted_model = data['fitted_model']
        self.order = data['order']
        self.seasonal_order = data['seasonal_order']
        self.hyperparameters = data['hyperparameters']
        self.is_trained = data['is_trained']
