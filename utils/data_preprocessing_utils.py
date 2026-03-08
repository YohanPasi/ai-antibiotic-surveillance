"""
Utility module for data preprocessing and feature engineering for AMR surveillance
This module provides helper functions for cleaning and transforming microbiological data
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Union
import re
import json
from pathlib import Path


class DataPreprocessor:
    """Handle data preprocessing for AMR surveillance models"""
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path) if config_path else {}
        self.organism_mapping = self._get_organism_mapping()
        self.antibiotic_mapping = self._get_antibiotic_mapping()
        
    def _load_config(self, path: str) -> Dict:
        """Load preprocessing configuration"""
        with open(path, 'r') as f:
            return json.load(f)
    
    def _get_organism_mapping(self) -> Dict:
        """Get standardized organism name mappings"""
        return {
            'staph aureus': 'Staphylococcus aureus',
            's. aureus': 'Staphylococcus aureus',
            'mrsa': 'Staphylococcus aureus (MRSA)',
            'e. coli': 'Escherichia coli',
            'e coli': 'Escherichia coli',
            'klebsiella': 'Klebsiella pneumoniae',
            'k. pneumoniae': 'Klebsiella pneumoniae',
            'pseudomonas': 'Pseudomonas aeruginosa',
            'p. aeruginosa': 'Pseudomonas aeruginosa',
            'acinetobacter': 'Acinetobacter baumannii',
            'a. baumannii': 'Acinetobacter baumannii',
            'streptococcus': 'Streptococcus pyogenes',
            's. pyogenes': 'Streptococcus pyogenes',
            'enterococcus': 'Enterococcus faecalis',
            'e. faecalis': 'Enterococcus faecalis'
        }
    
    def _get_antibiotic_mapping(self) -> Dict:
        """Get standardized antibiotic name mappings"""
        return {
            'amox': 'Amoxicillin',
            'amoxicillin': 'Amoxicillin',
            'amp': 'Ampicillin',
            'ampicillin': 'Ampicillin',
            'cef': 'Cefotaxime',
            'cefotaxime': 'Cefotaxime',
            'ceftriaxone': 'Ceftriaxone',
            'ceftazidime': 'Ceftazidime',
            'ciprofloxacin': 'Ciprofloxacin',
            'cipro': 'Ciprofloxacin',
            'gent': 'Gentamicin',
            'gentamicin': 'Gentamicin',
            'vancomycin': 'Vancomycin',
            'vanco': 'Vancomycin',
            'meropenem': 'Meropenem',
            'mero': 'Meropenem',
            'imipenem': 'Imipenem',
            'imi': 'Imipenem',
            'colistin': 'Colistin',
            'col': 'Colistin'
        }
    
    def clean_organism_name(self, name: str) -> str:
        """Standardize organism names"""
        if pd.isna(name):
            return None
        
        name_lower = name.lower().strip()
        return self.organism_mapping.get(name_lower, name)
    
    def clean_antibiotic_name(self, name: str) -> str:
        """Standardize antibiotic names"""
        if pd.isna(name):
            return None
        
        name_lower = name.lower().strip()
        return self.antibiotic_mapping.get(name_lower, name)
    
    def parse_susceptibility(self, value: str) -> str:
        """Parse and standardize susceptibility values (S/I/R)"""
        if pd.isna(value):
            return None
        
        value_clean = str(value).strip().upper()
        
        if value_clean in ['S', 'SENSITIVE', 'SUSCEPTIBLE']:
            return 'S'
        elif value_clean in ['I', 'INTERMEDIATE']:
            return 'I'
        elif value_clean in ['R', 'RESISTANT']:
            return 'R'
        else:
            return None
    
    def encode_sample_type(self, sample_type: str) -> int:
        """Encode sample types to numeric values"""
        encoding = {
            'Blood': 1,
            'Urine': 2,
            'Sputum': 3,
            'Wound': 4,
            'CSF': 5,
            'Other': 6
        }
        return encoding.get(sample_type, 6)
    
    def encode_ward(self, ward: str) -> int:
        """Encode ward names to numeric values"""
        encoding = {
            'ICU': 1,
            'Medical': 2,
            'Surgical': 3,
            'Pediatric': 4,
            'Maternity': 5,
            'Emergency': 6,
            'Other': 7
        }
        return encoding.get(ward, 7)
    
    def calculate_age_group(self, age: int) -> str:
        """Calculate age group from age"""
        if pd.isna(age):
            return 'Unknown'
        
        if age < 18:
            return 'Pediatric'
        elif age < 65:
            return 'Adult'
        else:
            return 'Elderly'
    
    def extract_temporal_features(self, date: datetime) -> Dict:
        """Extract temporal features from date"""
        return {
            'year': date.year,
            'month': date.month,
            'quarter': (date.month - 1) // 3 + 1,
            'week': date.isocalendar()[1],
            'day_of_week': date.weekday(),
            'is_weekend': date.weekday() >= 5
        }
    
    def calculate_hospital_stay_duration(self, admission_date: datetime, 
                                        sample_date: datetime) -> int:
        """Calculate hospital stay duration in days"""
        if pd.isna(admission_date) or pd.isna(sample_date):
            return None
        
        duration = (sample_date - admission_date).days
        return max(0, duration)
    
    def handle_missing_values(self, df: pd.DataFrame, 
                            strategy: str = 'median') -> pd.DataFrame:
        """Handle missing values in dataset"""
        df_copy = df.copy()
        
        if strategy == 'median':
            numeric_cols = df_copy.select_dtypes(include=[np.number]).columns
            df_copy[numeric_cols] = df_copy[numeric_cols].fillna(
                df_copy[numeric_cols].median()
            )
        elif strategy == 'mode':
            categorical_cols = df_copy.select_dtypes(include=['object']).columns
            df_copy[categorical_cols] = df_copy[categorical_cols].fillna(
                df_copy[categorical_cols].mode().iloc[0]
            )
        elif strategy == 'drop':
            df_copy = df_copy.dropna()
        
        return df_copy
    
    def detect_outliers(self, series: pd.Series, method: str = 'iqr') -> pd.Series:
        """Detect outliers using IQR or Z-score method"""
        if method == 'iqr':
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            return (series < lower_bound) | (series > upper_bound)
        elif method == 'zscore':
            z_scores = np.abs((series - series.mean()) / series.std())
            return z_scores > 3
        
        return pd.Series([False] * len(series))
    
    def create_resistance_score(self, susceptibilities: Dict[str, str]) -> float:
        """Calculate resistance score based on multiple antibiotics"""
        if not susceptibilities:
            return 0.0
        
        scores = {'S': 0, 'I': 0.5, 'R': 1}
        total_score = sum(scores.get(v, 0) for v in susceptibilities.values())
        return total_score / len(susceptibilities)
    
    def aggregate_weekly_data(self, df: pd.DataFrame, 
                             date_column: str = 'sample_date') -> pd.DataFrame:
        """Aggregate data by week"""
        df_copy = df.copy()
        df_copy['week'] = pd.to_datetime(df_copy[date_column]).dt.to_period('W')
        return df_copy.groupby('week').agg({
            'organism': 'count',
            'resistance_score': 'mean'
        }).reset_index()
    
    def create_lag_features(self, df: pd.DataFrame, columns: List[str], 
                           lags: List[int] = [1, 2, 3]) -> pd.DataFrame:
        """Create lagged features for time series data"""
        df_copy = df.copy()
        
        for col in columns:
            for lag in lags:
                df_copy[f'{col}_lag_{lag}'] = df_copy[col].shift(lag)
        
        return df_copy
    
    def calculate_rolling_statistics(self, df: pd.DataFrame, column: str,
                                    windows: List[int] = [7, 14, 30]) -> pd.DataFrame:
        """Calculate rolling mean and std for specified windows"""
        df_copy = df.copy()
        
        for window in windows:
            df_copy[f'{column}_rolling_mean_{window}'] = (
                df_copy[column].rolling(window=window).mean()
            )
            df_copy[f'{column}_rolling_std_{window}'] = (
                df_copy[column].rolling(window=window).std()
            )
        
        return df_copy
    
    def normalize_features(self, df: pd.DataFrame, columns: List[str],
                          method: str = 'minmax') -> pd.DataFrame:
        """Normalize numerical features"""
        df_copy = df.copy()
        
        if method == 'minmax':
            for col in columns:
                min_val = df_copy[col].min()
                max_val = df_copy[col].max()
                df_copy[f'{col}_normalized'] = (
                    (df_copy[col] - min_val) / (max_val - min_val)
                )
        elif method == 'standard':
            for col in columns:
                mean_val = df_copy[col].mean()
                std_val = df_copy[col].std()
                df_copy[f'{col}_normalized'] = (
                    (df_copy[col] - mean_val) / std_val
                )
        
        return df_copy
    
    def encode_categorical_features(self, df: pd.DataFrame, columns: List[str],
                                   method: str = 'onehot') -> pd.DataFrame:
        """Encode categorical features"""
        df_copy = df.copy()
        
        if method == 'onehot':
            df_copy = pd.get_dummies(df_copy, columns=columns, prefix=columns)
        elif method == 'label':
            for col in columns:
                df_copy[f'{col}_encoded'] = pd.Categorical(
                    df_copy[col]
                ).codes
        
        return df_copy
    
    def split_train_test(self, df: pd.DataFrame, test_size: float = 0.2,
                        time_based: bool = True, date_column: str = None):
        """Split data into train and test sets"""
        if time_based and date_column:
            df_sorted = df.sort_values(by=date_column)
            split_idx = int(len(df_sorted) * (1 - test_size))
            train = df_sorted.iloc[:split_idx]
            test = df_sorted.iloc[split_idx:]
        else:
            from sklearn.model_selection import train_test_split
            train, test = train_test_split(df, test_size=test_size, random_state=42)
        
        return train, test
    
    def validate_data_quality(self, df: pd.DataFrame) -> Dict:
        """Validate data quality and return report"""
        report = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'missing_values': df.isnull().sum().to_dict(),
            'duplicate_rows': df.duplicated().sum(),
            'data_types': df.dtypes.astype(str).to_dict()
        }
        
        return report
    
    def preprocess_pipeline(self, df: pd.DataFrame, 
                          config: Dict = None) -> pd.DataFrame:
        """Complete preprocessing pipeline"""
        df_processed = df.copy()
        
        # Clean organism and antibiotic names
        if 'organism' in df_processed.columns:
            df_processed['organism'] = df_processed['organism'].apply(
                self.clean_organism_name
            )
        
        if 'antibiotic' in df_processed.columns:
            df_processed['antibiotic'] = df_processed['antibiotic'].apply(
                self.clean_antibiotic_name
            )
        
        # Parse susceptibility
        if 'susceptibility' in df_processed.columns:
            df_processed['susceptibility'] = df_processed['susceptibility'].apply(
                self.parse_susceptibility
            )
        
        # Handle missing values
        df_processed = self.handle_missing_values(df_processed)
        
        # Extract temporal features
        if 'sample_date' in df_processed.columns:
            temporal_features = df_processed['sample_date'].apply(
                lambda x: self.extract_temporal_features(pd.to_datetime(x))
            )
            df_processed = pd.concat([
                df_processed,
                pd.DataFrame(temporal_features.tolist())
            ], axis=1)
        
        return df_processed


class FeatureEngineering:
    """Advanced feature engineering for AMR prediction models"""
    
    def __init__(self):
        self.feature_importance = {}
    
    def create_interaction_features(self, df: pd.DataFrame,
                                   feature_pairs: List[Tuple[str, str]]) -> pd.DataFrame:
        """Create interaction features between pairs of features"""
        df_copy = df.copy()
        
        for feat1, feat2 in feature_pairs:
            df_copy[f'{feat1}_x_{feat2}'] = df_copy[feat1] * df_copy[feat2]
        
        return df_copy
    
    def create_polynomial_features(self, df: pd.DataFrame, columns: List[str],
                                  degree: int = 2) -> pd.DataFrame:
        """Create polynomial features"""
        from sklearn.preprocessing import PolynomialFeatures
        
        df_copy = df.copy()
        poly = PolynomialFeatures(degree=degree, include_bias=False)
        poly_features = poly.fit_transform(df_copy[columns])
        
        feature_names = poly.get_feature_names_out(columns)
        poly_df = pd.DataFrame(poly_features, columns=feature_names,
                             index=df_copy.index)
        
        return pd.concat([df_copy, poly_df], axis=1)
    
    def create_domain_specific_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create domain-specific features for AMR surveillance"""
        df_copy = df.copy()
        
        # Prior antibiotic exposure risk score
        if 'prior_antibiotics' in df_copy.columns:
            df_copy['antibiotic_exposure_score'] = (
                df_copy['prior_antibiotics'].str.count(',') + 1
            )
        
        # Hospital-acquired infection indicator
        if 'hospital_stay_duration' in df_copy.columns:
            df_copy['is_hospital_acquired'] = (
                df_copy['hospital_stay_duration'] > 2
            ).astype(int)
        
        # High-risk ward indicator
        if 'ward' in df_copy.columns:
            high_risk_wards = ['ICU', 'Surgical', 'Burn Unit']
            df_copy['is_high_risk_ward'] = (
                df_copy['ward'].isin(high_risk_wards)
            ).astype(int)
        
        # Immunocompromised indicator
        if 'diagnosis' in df_copy.columns:
            immunocompromised_keywords = ['cancer', 'hiv', 'transplant', 'diabetes']
            df_copy['is_immunocompromised'] = df_copy['diagnosis'].str.lower().apply(
                lambda x: any(keyword in str(x) for keyword in immunocompromised_keywords)
            ).astype(int)
        
        return df_copy
    
    def calculate_resistance_trends(self, df: pd.DataFrame,
                                   organism: str,
                                   antibiotic: str) -> Dict:
        """Calculate resistance trends over time"""
        filtered = df[
            (df['organism'] == organism) &
            (df['antibiotic'] == antibiotic)
        ]
        
        if len(filtered) == 0:
            return {'trend': 'insufficient_data'}
        
        monthly_resistance = filtered.groupby(
            pd.Grouper(key='sample_date', freq='M')
        )['susceptibility'].apply(
            lambda x: (x == 'R').sum() / len(x) if len(x) > 0 else 0
        )
        
        # Calculate trend (increasing/decreasing/stable)
        if len(monthly_resistance) >= 3:
            recent_avg = monthly_resistance[-3:].mean()
            older_avg = monthly_resistance[:-3].mean() if len(monthly_resistance) > 3 else 0
            
            if recent_avg > older_avg * 1.1:
                trend = 'increasing'
            elif recent_avg < older_avg * 0.9:
                trend = 'decreasing'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'
        
        return {
            'trend': trend,
            'current_resistance_rate': monthly_resistance.iloc[-1] if len(monthly_resistance) > 0 else 0,
            'average_resistance_rate': monthly_resistance.mean()
        }
    
    def detect_outbreak_patterns(self, df: pd.DataFrame, threshold: float = 2.0) -> List[Dict]:
        """Detect potential outbreak patterns"""
        outbreaks = []
        
        # Group by organism and ward
        grouped = df.groupby(['organism', 'ward', pd.Grouper(key='sample_date', freq='W')])
        weekly_counts = grouped.size().reset_index(name='count')
        
        for (organism, ward), group in weekly_counts.groupby(['organism', 'ward']):
            mean_count = group['count'].mean()
            std_count = group['count'].std()
            
            if std_count > 0:
                z_scores = (group['count'] - mean_count) / std_count
                outbreak_weeks = group[z_scores > threshold]
                
                for _, row in outbreak_weeks.iterrows():
                    outbreaks.append({
                        'organism': organism,
                        'ward': ward,
                        'week': row['sample_date'],
                        'count': row['count'],
                        'expected_count': mean_count,
                        'z_score': (row['count'] - mean_count) / std_count
                    })
        
        return outbreaks


def main():
    """Main function for testing preprocessing"""
    # Example usage
    preprocessor = DataPreprocessor()
    
    # Sample data
    sample_data = pd.DataFrame({
        'organism': ['staph aureus', 'e. coli', 'pseudomonas'],
        'antibiotic': ['vancomycin', 'ceftriaxone', 'meropenem'],
        'susceptibility': ['S', 'R', 'I'],
        'sample_date': pd.date_range('2024-01-01', periods=3),
        'age': [45, 67, 23]
    })
    
    processed_data = preprocessor.preprocess_pipeline(sample_data)
    print("Processed Data Shape:", processed_data.shape)
    print("\nFirst few rows:")
    print(processed_data.head())


if __name__ == '__main__':
    main()
