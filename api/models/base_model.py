"""
Base Model Abstract Class
Defines the interface that all forecasting models must implement
"""
from abc import ABC, abstractmethod
import numpy as np
from typing import List, Tuple, Optional, Dict
import pandas as pd

class BaseModel(ABC):
    """
    Abstract base class for all AST prediction models.
    All models must implement fit, predict, and evaluate methods.
    """
    
    def __init__(self, name: str):
        """
        Initialize the model.
        
        Args:
            name: Model name (e.g., 'SMA', 'Prophet', 'ARIMA')
        """
        self.name = name
        self.is_trained = False
        self.hyperparameters = {}
        
    @abstractmethod
    def fit(self, historical_data: pd.DataFrame) -> None:
        """
        Train the model on historical data.
        
        Args:
            historical_data: DataFrame with columns ['week_start_date', 'susceptibility_percent']
                           Index should be datetime, sorted chronologically
        """
        pass
    
    @abstractmethod
    def predict(self, steps: int = 1) -> Tuple[float, Optional[float], Optional[float]]:
        """
        Generate prediction for next week(s).
        
        Args:
            steps: Number of weeks ahead to predict (default: 1)
            
        Returns:
            Tuple of (predicted_value, lower_bound, upper_bound)
            If uncertainty not available, bounds can be None
        """
        pass
    
    def evaluate(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """
        Evaluate model performance using multiple metrics.
        
        Args:
            y_true: Actual values
            y_pred: Predicted values
            
        Returns:
            Dictionary of evaluation metrics
        """
        # Remove NaN values
        mask = ~(np.isnan(y_true) | np.isnan(y_pred))
        y_true_clean = y_true[mask]
        y_pred_clean = y_pred[mask]
        
        if len(y_true_clean) == 0:
            return {
                'mae': np.nan,
                'rmse': np.nan,
                'mape': np.nan,
                'r2': np.nan
            }
        
        # Mean Absolute Error
        mae = np.mean(np.abs(y_true_clean - y_pred_clean))
        
        # Root Mean Squared Error
        rmse = np.sqrt(np.mean((y_true_clean - y_pred_clean) ** 2))
        
        # Mean Absolute Percentage Error (handle division by zero)
        mape = np.mean(np.abs((y_true_clean - y_pred_clean) / np.where(y_true_clean != 0, y_true_clean, 1))) * 100
        
        # R-squared
        ss_res = np.sum((y_true_clean - y_pred_clean) ** 2)
        ss_tot = np.sum((y_true_clean - np.mean(y_true_clean)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        return {
            'mae': mae,
            'rmse': rmse,
            'mape': mape,
            'r2': r2
        }
    
    @abstractmethod
    def save_model(self, filepath: str) -> None:
        """
        Save the trained model to disk.
        
        Args:
            filepath: Path where model should be saved
        """
        pass
    
    @abstractmethod
    def load_model(self, filepath: str) -> None:
        """
        Load a trained model from disk.
        
        Args:
            filepath: Path to the saved model
        """
        pass
    
    def get_info(self) -> Dict:
        """
        Get model information and hyperparameters.
        
        Returns:
            Dictionary with model metadata
        """
        return {
            'name': self.name,
            'is_trained': self.is_trained,
            'hyperparameters': self.hyperparameters
        }
