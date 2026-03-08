"""
Model evaluation and metrics module for AMR surveillance models
Provides comprehensive evaluation metrics and visualization tools
"""

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
    mean_squared_error, mean_absolute_error, r2_score
)
from sklearn.model_selection import cross_val_score, KFold
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import json


class ModelEvaluator:
    """Comprehensive model evaluation for AMR prediction models"""
    
    def __init__(self, model_name: str = ""):
        self.model_name = model_name
        self.metrics_history = []
        
    def calculate_classification_metrics(self, y_true: np.ndarray,
                                        y_pred: np.ndarray,
                                        y_prob: np.ndarray = None) -> Dict:
        """Calculate all classification metrics"""
        metrics = {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, average='weighted', zero_division=0),
            'recall': recall_score(y_true, y_pred, average='weighted', zero_division=0),
            'f1_score': f1_score(y_true, y_pred, average='weighted', zero_division=0),
            'confusion_matrix': confusion_matrix(y_true, y_pred).tolist()
        }
        
        if y_prob is not None:
            try:
                metrics['roc_auc'] = roc_auc_score(y_true, y_prob, multi_class='ovr')
            except:
                metrics['roc_auc'] = None
        
        return metrics
    
    def calculate_regression_metrics(self, y_true: np.ndarray,
                                    y_pred: np.ndarray) -> Dict:
        """Calculate regression metrics"""
        metrics = {
            'mse': mean_squared_error(y_true, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
            'mae': mean_absolute_error(y_true, y_pred),
            'r2': r2_score(y_true, y_pred),
            'mape': np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        }
        
        return metrics
    
    def cross_validate_model(self, model, X, y, cv: int = 5) -> Dict:
        """Perform k-fold cross-validation"""
        kfold = KFold(n_splits=cv, shuffle=True, random_state=42)
        
        scores = {
            'accuracy': cross_val_score(model, X, y, cv=kfold, scoring='accuracy'),
            'precision': cross_val_score(model, X, y, cv=kfold, scoring='precision_weighted'),
            'recall': cross_val_score(model, X, y, cv=kfold, scoring='recall_weighted'),
            'f1': cross_val_score(model, X, y, cv=kfold, scoring='f1_weighted')
        }
        
        results = {
            'mean_accuracy': scores['accuracy'].mean(),
            'std_accuracy': scores['accuracy'].std(),
            'mean_precision': scores['precision'].mean(),
            'std_precision': scores['precision'].std(),
            'mean_recall': scores['recall'].mean(),
            'std_recall': scores['recall'].std(),
            'mean_f1': scores['f1'].mean(),
            'std_f1': scores['f1'].std()
        }
        
        return results
    
    def calculate_confusion_matrix_metrics(self, cm: np.ndarray) -> Dict:
        """Extract detailed metrics from confusion matrix"""
        tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)
        
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
        sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
        ppv = tp / (tp + fp) if (tp + fp) > 0 else 0
        npv = tn / (tn + fn) if (tn + fn) > 0 else 0
        
        return {
            'true_positive': int(tp),
            'true_negative': int(tn),
            'false_positive': int(fp),
            'false_negative': int(fn),
            'sensitivity': sensitivity,
            'specificity': specificity,
            'ppv': ppv,
            'npv': npv
        }
    
    def evaluate_time_series_model(self, y_true: np.ndarray, y_pred: np.ndarray,
                                  seasonality: int = None) -> Dict:
        """Evaluate time series forecasting model"""
        metrics  = self.calculate_regression_metrics(y_true, y_pred)
        
        # Add time series specific metrics
        residuals = y_true - y_pred
        metrics['mean_residual'] = np.mean(residuals)
        metrics['std_residual'] = np.std(residuals)
        
        if seasonality:
            seasonal_error = np.mean(np.abs(residuals[:seasonality]))
            metrics['seasonal_error'] = seasonal_error
        
        return metrics
    
    def calculate_feature_importance(self, model, feature_names: List[str],
                                    method: str = 'builtin') -> pd.DataFrame:
        """Calculate and rank feature importance"""
        if method == 'builtin' and hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
        elif method == 'coef' and hasattr(model, 'coef_'):
            importances = np.abs(model.coef_[0]) if model.coef_.ndim > 1 else np.abs(model.coef_)
        else:
            return pd.DataFrame()
        
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': importances
        }).sort_values('importance', ascending=False)
        
        return importance_df
    
    def plot_confusion_matrix(self, cm: np.ndarray, classes: List[str],
                             save_path: str = None) -> None:
        """Plot confusion matrix"""
        plt.figure(figsize=(10, 8))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                   xticklabels=classes, yticklabels=classes)
        plt.ylabel('Actual')
        plt.xlabel('Predicted')
        plt.title(f'Confusion Matrix - {self.model_name}')
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_roc_curve(self, y_true: np.ndarray, y_prob: np.ndarray,
                      save_path: str = None) -> None:
        """Plot ROC curve"""
        from sklearn.metrics import roc_curve, auc
        
        fpr, tpr, _ = roc_curve(y_true, y_prob)
        roc_auc = auc(fpr, tpr)
        
        plt.figure(figsize=(10, 8))
        plt.plot(fpr, tpr, color='darkorange', lw=2,
                label=f'ROC curve (AUC = {roc_auc:.2f})')
        plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title(f'ROC Curve - {self.model_name}')
        plt.legend(loc="lower right")
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_feature_importance(self, importance_df: pd.DataFrame,
                               top_n: int = 20, save_path: str = None) -> None:
        """Plot feature importance"""
        plt.figure(figsize=(12, 8))
        top_features = importance_df.head(top_n)
        plt.barh(range(len(top_features)), top_features['importance'])
        plt.yticks(range(len(top_features)), top_features['feature'])
        plt.xlabel('Importance')
        plt.title(f'Top {top_n} Features - {self.model_name}')
        plt.gca().invert_yaxis()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_prediction_vs_actual(self, y_true: np.ndarray, y_pred: np.ndarray,
                                 save_path: str = None) -> None:
        """Plot predicted vs actual values"""
        plt.figure(figsize=(10, 8))
        plt.scatter(y_true, y_pred, alpha=0.5)
        plt.plot([y_true.min(), y_true.max()],
                [y_true.min(), y_true.max()],
                'r--', lw=2)
        plt.xlabel('Actual Values')
        plt.ylabel('Predicted Values')
        plt.title(f'Predicted vs Actual - {self.model_name}')
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_residuals(self, y_true: np.ndarray, y_pred: np.ndarray,
                      save_path: str = None) -> None:
        """Plot residual distribution"""
        residuals = y_true - y_pred
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
        
        # Residual plot
        ax1.scatter(y_pred, residuals, alpha=0.5)
        ax1.axhline(y=0, color='r', linestyle='--')
        ax1.set_xlabel('Predicted Values')
        ax1.set_ylabel('Residuals')
        ax1.set_title('Residual Plot')
        
        # Residual distribution
        ax2.hist(residuals, bins=50, edgecolor='black')
        ax2.set_xlabel('Residuals')
        ax2.set_ylabel('Frequency')
        ax2.set_title('Residual Distribution')
        
        plt.suptitle(f'Residual Analysis - {self.model_name}')
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def generate_evaluation_report(self, metrics: Dict, save_path: str = None) -> str:
        """Generate comprehensive evaluation report"""
        report = f"""
{'='*80}
Model Evaluation Report: {self.model_name}
{'='*80}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

CLASSIFICATION METRICS:
{'-'*80}
Accuracy:     {metrics.get('accuracy', 'N/A'):.4f}
Precision:    {metrics.get('precision', 'N/A'):.4f}
Recall:       {metrics.get('recall', 'N/A'):.4f}
F1 Score:     {metrics.get('f1_score', 'N/A'):.4f}
ROC AUC:      {metrics.get('roc_auc', 'N/A'):.4f if metrics.get('roc_auc') else 'N/A'}

CONFUSION MATRIX METRICS:
{'-'*80}
True Positive:  {metrics.get('true_positive', 'N/A')}
True Negative:  {metrics.get('true_negative', 'N/A')}
False Positive: {metrics.get('false_positive', 'N/A')}
False Negative: {metrics.get('false_negative', 'N/A')}
Sensitivity:    {metrics.get('sensitivity', 'N/A'):.4f if 'sensitivity' in metrics else 'N/A'}
Specificity:    {metrics.get('specificity', 'N/A'):.4f if 'specificity' in metrics else 'N/A'}
PPV:            {metrics.get('ppv', 'N/A'):.4f if 'ppv' in metrics else 'N/A'}
NPV:            {metrics.get('npv', 'N/A'):.4f if 'npv' in metrics else 'N/A'}

{'='*80}
"""
        
        if save_path:
            with open(save_path, 'w') as f:
                f.write(report)
        
        return report
    
    def save_metrics_to_json(self, metrics: Dict, file_path: str) -> None:
        """Save metrics to JSON file"""
        metrics_with_metadata = {
            'model_name': self.model_name,
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics
        }
        
        with open(file_path, 'w') as f:
            json.dump(metrics_with_metadata, f, indent=4)
    
    def compare_multiple_models(self, models_metrics: Dict[str, Dict]) -> pd.DataFrame:
        """Compare metrics across multiple models"""
        comparison_data = []
        
        for model_name, metrics in models_metrics.items():
            row = {'Model': model_name}
            row.update(metrics)
            comparison_data.append(row)
        
        comparison_df = pd.DataFrame(comparison_data)
        return comparison_df.set_index('Model')
    
    def calculate_clinical_impact_metrics(self, y_true: np.ndarray,
                                         y_pred: np.ndarray,
                                         costs: Dict = None) -> Dict:
        """Calculate clinical impact metrics"""
        if costs is None:
            costs = {
                'tp': 100,   # Correctly identified resistant case
                'tn': 50,    # Correctly identified susceptible case
                'fp': -200,  # False alarm cost
                'fn': -500   # Missed resistant case cost
            }
        
        cm = confusion_matrix(y_true, y_pred)
        tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)
        
        total_cost = (tp * costs['tp'] + tn * costs['tn'] + 
                     fp * costs['fp'] + fn * costs['fn'])
        
        # Calculate potential lives saved/improved
        lives_saved_estimate = tp * 0.8  # Assume 80% better outcome with early detection
        avoided_outbreaks = (tp + tn) * 0.1  # 10% outbreak prevention rate
        
        return {
            'total_clinical_value': total_cost,
            'estimated_lives_saved': lives_saved_estimate,
            'estimated_outbreaks_prevented': avoided_outbreaks,
            'cost_per_prediction': total_cost / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
        }
    
    def track_model_performance_over_time(self, metrics: Dict,
                                         timestamp: datetime = None) -> None:
        """Track model performance metrics over time"""
        if timestamp is None:
            timestamp = datetime.now()
        
        metrics_entry = {
            'timestamp': timestamp.isoformat(),
            **metrics
        }
        
        self.metrics_history.append(metrics_entry)
    
    def detect_model_drift(self, baseline_metrics: Dict,
                          current_metrics: Dict,
                          threshold: float = 0.05) -> Dict:
        """Detect model performance drift"""
        drift_detected = False
        drifted_metrics = []
        
        for metric_name in ['accuracy', 'precision', 'recall', 'f1_score']:
            if metric_name in baseline_metrics and metric_name in current_metrics:
                baseline_val = baseline_metrics[metric_name]
                current_val = current_metrics[metric_name]
                
                if abs(baseline_val - current_val) > threshold:
                    drift_detected = True
                    drifted_metrics.append({
                        'metric': metric_name,
                        'baseline': baseline_val,
                        'current': current_val,
                        'difference': current_val - baseline_val
                    })
        
        return {
            'drift_detected': drift_detected,
            'drifted_metrics': drifted_metrics,
            'recommendation': 'Retrain model' if drift_detected else 'Model performing well'
        }
    
    def calculate_calibration_metrics(self, y_true: np.ndarray,
                                     y_prob: np.ndarray,
                                     n_bins: int = 10) -> Dict:
        """Calculate model calibration metrics"""
        from sklearn.calibration import calibration_curve
        
        prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=n_bins)
        
        # Calculate calibration error
        calibration_error = np.mean(np.abs(prob_true - prob_pred))
        
        return {
            'calibration_error': calibration_error,
            'prob_true': prob_true.tolist(),
            'prob_pred': prob_pred.tolist()
        }


class ModelBenchmark:
    """Benchmark models against baseline and best practices"""
    
    def __init__(self):
        self.baseline_metrics = {}
        self.benchmark_results = []
    
    def set_baseline(self, metrics: Dict) -> None:
        """Set baseline metrics for comparison"""
        self.baseline_metrics = metrics
    
    def compare_to_baseline(self, model_metrics: Dict) -> Dict:
        """Compare model metrics to baseline"""
        comparison = {}
        
        for metric, value in model_metrics.items():
            if metric in self.baseline_metrics:
                baseline_value = self.baseline_metrics[metric]
                improvement = ((value - baseline_value) / baseline_value * 100 
                             if baseline_value != 0 else 0)
                comparison[metric] = {
                    'current': value,
                    'baseline': baseline_value,
                    'improvement_%': improvement
                }
        
        return comparison
    
    def calculate_statistical_significance(self, metrics1: List[float],
                                          metrics2: List[float]) -> Dict:
        """Calculate statistical significance between two sets of metrics"""
        from scipy import stats
        
        t_stat, p_value = stats.ttest_ind(metrics1, metrics2)
        
        return {
            't_statistic': t_stat,
            'p_value': p_value,
            'significant': p_value < 0.05,
            'mean_diff': np.mean(metrics1) - np.mean(metrics2)
        }


def main():
    """Main function for testing evaluator"""
    # Example usage
    evaluator = ModelEvaluator(model_name="MRSA_XGBoost_v1")
    
    # Generate dummy data
    np.random.seed(42)
    y_true = np.random.randint(0, 2, 100)
    y_pred = np.random.randint(0, 2, 100)
    y_prob = np.random.random(100)
    
    # Calculate metrics
    metrics = evaluator.calculate_classification_metrics(y_true, y_pred, y_prob)
    
    print("Classification Metrics:")
    for key, value in metrics.items():
        if key != 'confusion_matrix':
            print(f"{key}: {value}")
    
    # Generate report
    report = evaluator.generate_evaluation_report(metrics)
    print(report)


if __name__ == '__main__':
    main()
