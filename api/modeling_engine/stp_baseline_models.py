
"""
STP Stage 3: Baseline Models (M32)
---------------------------------
Naive comparators for ML evaluation.
ENFORCES M32: All ML models must be compared against simple baselines.
"""

import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin

class NaiveLastValueClassifier(BaseEstimator, ClassifierMixin):
    """
    Predicts class based on the last observed value (Rate > Threshold).
    Essentially: Is the current rate > threshold? Then predict 1 for next week.
    """
    def __init__(self, threshold=0.30):
        self.threshold = threshold
        
    def fit(self, X, y=None):
        return self
        
    def predict_proba(self, X):
        # X should contain 'resistance_rate' (current/lag0) column
        # Or 'resistance_rate_lag1' if X is purely past features.
        # Assuming 'resistance_rate_lag1' (T-1) is the most recent known value 
        # for a forecast at T from T-1 data?
        # Actually, if we forecast T+1 at time T, we know Rate(T).
        # We assume X has 'current_resistance_rate'
        
        # Heuristic: return 0.9 if > threshold, 0.1 if <= threshold
        # to simulate probability for metrics like AUC.
        # Ideally, we return the rate itself as the probability proxy.
        
        if 'resistance_rate' in X.columns:
            probs = X['resistance_rate'].clip(0, 1).values
        elif 'resistance_rate_lag1' in X.columns:
             probs = X['resistance_rate_lag1'].clip(0, 1).values
        else:
            raise ValueError("Naive predictor requires 'resistance_rate' feature.")
            
        # Return N x 2 array [P(0), P(1)]
        return np.column_stack((1 - probs, probs))
        
    def predict(self, X):
        probs = self.predict_proba(X)[:, 1]
        return (probs >= self.threshold).astype(int)

class RollingMeanClassifier(BaseEstimator, ClassifierMixin):
    """
    Predicts probability = Rolling Mean of last N weeks.
    """
    def __init__(self, window=4):
        self.window = window
        
    def fit(self, X, y=None):
        return self
        
    def predict_proba(self, X):
        # Requires pre-calculated rolling mean features
        col_name = f'rolling_mean_{self.window}w'
        
        # If not present, we assume standard feature set has it or we can't run.
        # For simplicity, if we rely on Lag features, average Lag1..LagN
        
        cols = [f'resistance_rate_lag{i}' for i in range(1, self.window + 1)]
        available_cols = [c for c in cols if c in X.columns]
        
        if len(available_cols) < 1:
            # Fallback
            return NaiveLastValueClassifier().predict_proba(X)
            
        mean_rate = X[available_cols].mean(axis=1).fillna(0).values
        return np.column_stack((1 - mean_rate, mean_rate))
        
    def predict(self, X):
        # Use implicit 0.5 or passed threshold? 
        # Usually baseline just outputs prob.
        return (self.predict_proba(X)[:, 1] >= 0.3).astype(int) # arbitrary
