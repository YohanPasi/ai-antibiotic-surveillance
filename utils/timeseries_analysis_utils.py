"""
Time Series Analysis Utilities for AMR Surveillance
Provides forecasting and trend analysis for outbreak detection
"""

import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller, acf, pacf
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.metrics import mean_squared_error, mean_absolute_error
from scipy import stats
from typing import List, Dict, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class TimeSeriesAnalyzer:
    """Time series analysis for infection outbreak detection"""
    
    def __init__(self, data: pd.Series):
        self.data = data
        self.is_stationary = None
        self.trend_component = None
        self.seasonal_component = None
        self.residual_component = None
    
    def check_stationarity(self, significance_level: float = 0.05) -> Dict:
        """Perform Augmented Dickey-Fuller test for stationarity"""
        result= adfuller(self.data.dropna())
        
        self.is_stationary = result[1] < significance_level
        
        return {
            'is_stationary': self.is_stationary,
            'adf_statistic': result[0],
            'p_value': result[1],
            'critical_values': result[4],
            'interpretation': 'Stationary' if self.is_stationary else 'Non-stationary'
        }
    
    def make_stationary(self, method: str = 'diff') -> pd.Series:
        """Transform series to stationary"""
        if method == 'diff':
            return self.data.diff().dropna()
        elif method == 'log':
            return np.log(self.data + 1)
        elif method == 'log_diff':
            return np.log(self.data + 1).diff().dropna()
        else:
            return self.data
    
    def decompose_series(self, period: int = 7, model: str = 'additive') -> Dict:
        """Decompose time series into trend, seasonal, and residual components"""
        decomposition = seasonal_decompose(
            self.data,
            model=model,
            period=period,
            extrapolate_trend='freq'
        )
        
        self.trend_component = decomposition.trend
        self.seasonal_component = decomposition.seasonal
        self.residual_component = decomposition.resid
        
        return {
            'trend': self.trend_component,
            'seasonal': self.seasonal_component,
            'residual': self.residual_component
        }
    
    def detect_anomalies(self, threshold: float = 3.0) -> List[int]:
        """Detect anomalies using statistical methods"""
        mean = self.data.mean()
        std = self.data.std()
        
        z_scores = np.abs((self.data - mean) / std)
        anomaly_indices = np.where(z_scores > threshold)[0]
        
        return anomaly_indices.tolist()
    
    def detect_changepoints(self, penalty: float = 1.0) -> List[int]:
        """Detect change points in time series"""
        # Simple moving average based change point detection
        window = 7
        ma = self.data.rolling(window=window).mean()
        ma_diff = ma.diff().abs()
        
        threshold = ma_diff.mean() + penalty * ma_diff.std()
        changepoints = np.where(ma_diff > threshold)[0]
        
        return changepoints.tolist()
    
    def calculate_acf_pacf(self, nlags: int = 40) -> Dict:
        """Calculate ACF and PACF"""
        acf_values = acf(self.data.dropna(), nlags=nlags)
        pacf_values = pacf(self.data.dropna(), nlags=nlags)
        
        return {
            'acf': acf_values.tolist(),
            'pacf': pacf_values.tolist()
        }
    
    def identify_seasonality(self) -> Dict:
        """Identify seasonal patterns"""
        # Use FFT to detect dominant frequencies
        fft = np.fft.fft(self.data.values)
        power = np.abs(fft) ** 2
        frequencies = np.fft.fftfreq(len(self.data))
        
        # Find dominant frequency (excluding DC component)
        positive_freq_idx = np.where(frequencies > 0)[0]
        dominant_freq_idx = positive_freq_idx[np.argmax(power[positive_freq_idx])]
        dominant_period = 1 / frequencies[dominant_freq_idx] if frequencies[dominant_freq_idx] != 0 else 0
        
        return {
            'has_seasonality': power[dominant_freq_idx] > power.mean() * 2,
            'dominant_period': int(dominant_period),
            'strength': float(power[dominant_freq_idx] / power.mean())
        }


class ForecastingModel:
    """Forecasting models for outbreak prediction"""
    
    def __init__(self, data: pd.Series):
        self.data = data
        self.model = None
        self.fitted_values = None
        self.forecast = None
    
    def fit_arima(self, order: Tuple[int, int, int] = (1, 1, 1)) -> 'ForecastingModel':
        """Fit ARIMA model"""
        self.model = ARIMA(self.data, order=order)
        self.model = self.model.fit()
        self.fitted_values = self.model.fittedvalues
        return self
    
    def fit_exponential_smoothing(self, seasonal_periods: int = 7,
                                  trend: str = 'add',
                                  seasonal: str = 'add') -> 'ForecastingModel':
        """Fit Exponential Smoothing model"""
        self.model = ExponentialSmoothing(
            self.data,
            seasonal_periods=seasonal_periods,
            trend=trend,
            seasonal=seasonal
        )
        self.model = self.model.fit()
        self.fitted_values = self.model.fittedvalues
        return self
    
    def predict(self, steps: int = 7) -> pd.Series:
        """Generate forecast"""
        if self.model is None:
            raise ValueError("Model not fitted. Call fit method first.")
        
        self.forecast = self.model.forecast(steps=steps)
        return self.forecast
    
    def calculate_forecast_intervals(self, steps: int = 7,
                                    alpha: float = 0.05) -> Dict:
        """Calculate prediction intervals"""
        if self.model is None:
            raise ValueError("Model not fitted. Call fit method first.")
        
        forecast_result = self.model.get_forecast(steps=steps)
        forecast_mean = forecast_result.predicted_mean
        forecast_ci = forecast_result.conf_int(alpha=alpha)
        
        return {
            'mean': forecast_mean,
            'lower_bound': forecast_ci.iloc[:, 0],
            'upper_bound': forecast_ci.iloc[:, 1]
        }
    
    def evaluate_forecast(self, actual: pd.Series) -> Dict:
        """Evaluate forecast accuracy"""
        if self.forecast is None:
            raise ValueError("No forecast available. Call predict first.")
        
        # Align actual and forecast
        min_len = min(len(actual), len(self.forecast))
        actual_aligned = actual.iloc[:min_len]
        forecast_aligned = self.forecast.iloc[:min_len]
        
        mae = mean_absolute_error(actual_aligned, forecast_aligned)
        mse = mean_squared_error(actual_aligned, forecast_aligned)
        rmse = np.sqrt(mse)
        mape = np.mean(np.abs((actual_aligned - forecast_aligned) / actual_aligned)) * 100
        
        return {
            'mae': mae,
            'mse': mse,
            'rmse': rmse,
            'mape': mape
        }


class OutbreakDetector:
    """Detect disease outbreaks using time series analysis"""
    
    def __init__(self, baseline_data: pd.Series):
        self.baseline_data = baseline_data
        self.baseline_mean = baseline_data.mean()
        self.baseline_std = baseline_data.std()
    
    def detect_outbreak_zscore(self, current_value: float,
                              threshold: float = 2.0) -> Dict:
        """Detect outbreak using Z-score method"""
        z_score = (current_value - self.baseline_mean) / self.baseline_std
        is_outbreak = z_score > threshold
        
        return {
            'is_outbreak': bool(is_outbreak),
            'z_score': float(z_score),
            'current_value': current_value,
            'baseline_mean': self.baseline_mean,
            'severity': 'High' if z_score > 3 else 'Medium' if z_score > 2 else 'Low'
        }
    
    def detect_outbreak_ewma(self, recent_data: pd.Series,
                            lambda_param: float = 0.3,
                            L: float = 3) -> Dict:
        """Detect outbreak using EWMA control chart"""
        ewma = recent_data.ewm(alpha=lambda_param).mean()
        
        sigma = self.baseline_std * np.sqrt(lambda_param / (2 - lambda_param))
        ucl = self.baseline_mean + L * sigma
        lcl = self.baseline_mean - L * sigma
        
        violation_indices = np.where((ewma > ucl) | (ewma < lcl))[0]
        
        return {
            'is_outbreak': len(violation_indices) > 0,
            'ewma_values': ewma.tolist(),
            'ucl': ucl,
            'lcl': lcl,
            'violation_points': violation_indices.tolist()
        }
    
    def detect_outbreak_cusum(self, recent_data: pd.Series,
                             k: float = 0.5,
                             h: float = 5) -> Dict:
        """Detect outbreak using CUSUM method"""
        cusum_pos = np.zeros(len(recent_data))
        cusum_neg = np.zeros(len(recent_data))
        
        target = self.baseline_mean
        
        for i in range(1, len(recent_data)):
            cusum_pos[i] = max(0, cusum_pos[i-1] + recent_data.iloc[i] - target - k)
            cusum_neg[i] = max(0, cusum_neg[i-1] - recent_data.iloc[i] + target - k)
        
        outbreak_detected = (cusum_pos > h).any() or (cusum_neg > h).any()
        
        return {
            'is_outbreak': bool(outbreak_detected),
            'cusum_positive': cusum_pos.tolist(),
            'cusum_negative': cusum_neg.tolist(),
            'threshold': h
        }
    
    def assess_outbreak_severity(self, current_value: float,
                                historical_max: float) -> str:
        """Assess severity of outbreak"""
        ratio = current_value / self.baseline_mean
        
        if ratio >= 3:
            return 'Critical'
        elif ratio >= 2:
            return 'Severe'
        elif ratio >= 1.5:
            return 'Moderate'
        elif ratio >= 1.2:
            return 'Mild'
        else:
            return 'Normal'


class TrendAnalyzer:
    """Analyze trends in resistance patterns"""
    
    def __init__(self, data: pd.Series):
        self.data = data
    
    def calculate_trend_direction(self) -> str:
        """Determine overall trend direction"""
        # Linear regression on time index
        x = np.arange(len(self.data))
        y = self.data.values
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        if p_value > 0.05:
            return 'Stable'
        elif slope > 0:
            return 'Increasing'
        else:
            return 'Decreasing'
    
    def calculate_trend_strength(self) -> Dict:
        """Calculate strength of trend"""
        x = np.arange(len(self.data))
        y = self.data.values
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        return {
            'slope': slope,
            'r_squared': r_value ** 2,
            'p_value': p_value,
            'strength': 'Strong' if abs(r_value) > 0.7 else 'Moderate' if abs(r_value) > 0.4 else 'Weak'
        }
    
    def detect_trend_reversal(self, window: int = 7) -> List[int]:
        """Detect trend reversals"""
        # Calculate rolling mean
        ma = self.data.rolling(window=window).mean()
        
        # Calculate differences
        ma_diff = ma.diff()
        
        # Detect sign changes
        sign_changes = np.where(np.diff(np.sign(ma_diff.dropna())))[0]
        
        return sign_changes.tolist()
    
    def project_future_trend(self, periods: int = 30) -> pd.Series:
        """Project trend into future"""
        x = np.arange(len(self.data))
        y = self.data.values
        
        slope, intercept, _, _, _ = stats.linregress(x, y)
        
        future_x = np.arange(len(self.data), len(self.data) + periods)
        future_y = slope * future_x + intercept
        
        future_index = pd.date_range(
            start=self.data.index[-1] + pd.Timedelta(days=1),
            periods=periods
        )
        
        return pd.Series(future_y, index=future_index)


class SeasonalityAnalyzer:
    """Analyze seasonal patterns in resistance data"""
    
    def __init__(self, data: pd.Series):
        self.data = data
    
    def extract_seasonal_component(self, period: int = 7) -> pd.Series:
        """Extract seasonal component"""
        decomposition = seasonal_decompose(
            self.data,
            model='additive',
            period=period,
            extrapolate_trend='freq'
        )
        return decomposition.seasonal
    
    def calculate_seasonal_strength(self, period: int = 7) -> float:
        """Calculate strength of seasonality"""
        decomposition = seasonal_decompose(
            self.data,
            model='additive',
            period=period,
            extrapolate_trend='freq'
        )
        
        seasonal_var = decomposition.seasonal.var()
        residual_var = decomposition.resid.var()
        
        strength = 1 - (residual_var / (seasonal_var + residual_var))
        return max(0, min(1, strength))
    
    def identify_peak_seasons(self, period: int = 7) -> Dict:
        """Identify peak infection seasons"""
        seasonal = self.extract_seasonal_component(period)
        
        # Reshape to seasonal periods
        n_periods = len(seasonal) // period
        seasonal_matrix = seasonal.values[:n_periods * period].reshape(n_periods, period)
        
        # Average across all periods
        avg_seasonal = seasonal_matrix.mean(axis=0)
        
        peak_day = np.argmax(avg_seasonal)
        trough_day = np.argmin(avg_seasonal)
        
        return {
            'peak_day': int(peak_day),
            'trough_day': int(trough_day),
            'seasonal_pattern': avg_seasonal.tolist()
        }


class CorrelationAnalyzer:
    """Analyze correlations between different organisms/wards"""
    
    def __init__(self, data: pd.DataFrame):
        self.data = data
    
    def calculate_cross_correlation(self, series1: pd.Series,
                                   series2: pd.Series,
                                   max_lag: int = 7) -> Dict:
        """Calculate cross-correlation with lags"""
        correlations = []
        lags = range(-max_lag, max_lag + 1)
        
        for lag in lags:
            if lag < 0:
                corr = series1[:-lag].corr(series2[:lag])
            elif lag > 0:
                corr = series1[lag:].corr(series2[:-lag])
            else:
                corr = series1.corr(series2)
            
            correlations.append(corr)
        
        max_corr_idx = np.argmax(np.abs(correlations))
        max_corr = correlations[max_corr_idx]
        max_lag = lags[max_corr_idx]
        
        return {
            'all_correlations': correlations,
            'lags': list(lags),
            'max_correlation': max_corr,
            'max_correlation_lag': max_lag
        }
    
    def identify_leading_indicators(self, target_series: pd.Series,
                                   predictor_series: List[pd.Series],
                                   predictor_names: List[str]) -> pd.DataFrame:
        """Identify which series lead the target"""
        results = []
        
        for name, series in zip(predictor_names, predictor_series):
            cross_corr = self.calculate_cross_correlation(series, target_series)
            
            results.append({
                'predictor': name,
                'max_correlation': cross_corr['max_correlation'],
                'optimal_lag': cross_corr['max_correlation_lag'],
                'is_leading': cross_corr['max_correlation_lag'] > 0
            })
        
        return pd.DataFrame(results).sort_values('max_correlation', ascending=False)


def main():
    """Example usage of time series utilities"""
    # Generate sample data
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    values = np.random.poisson(10, 100) + np.sin(np.arange(100) * 2 * np.pi / 7) * 3
    data = pd.Series(values, index=dates)
    
    # Analyze time series
    analyzer = TimeSeriesAnalyzer(data)
    stationarity = analyzer.check_stationarity()
    print("Stationarity Check:", stationarity)
    
    seasonality = analyzer.identify_seasonality()
    print("Seasonality:", seasonality)
    
    anomalies = analyzer.detect_anomalies()
    print(f"Anomalies detected at indices: {anomalies}")
    
    # Forecasting
    forecaster = ForecastingModel(data)
    forecaster.fit_arima(order=(1, 0, 1))
    forecast = forecaster.predict(steps=7)
    print(f"\nForecast for next 7 days:\n{forecast}")
    
    # Outbreak detection
    detector = OutbreakDetector(data[:80])
    outbreak = detector.detect_outbreak_zscore(current_value=20)
    print(f"\nOutbreak Detection: {outbreak}")


if __name__ == '__main__':
    main()
