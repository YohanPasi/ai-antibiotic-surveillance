"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Union
from datetime import date, datetime

# ============================================
# Request Schemas
# ============================================

class PredictionRequest(BaseModel):
    """Request schema for prediction endpoint"""
    ward: Optional[str] = Field(None, description="Ward identifier (None for organism-level)")
    organism: str = Field(..., description="Organism name (e.g., 'Pseudomonas aeruginosa')")
    antibiotic: str = Field(..., description="Antibiotic name (e.g., 'Meropenem (MEM)')")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ward": "ICU",
                "organism": "Pseudomonas aeruginosa",
                "antibiotic": "Meropenem (MEM)"
            }
        }

class AntibioticResult(BaseModel):
    """Single antibiotic result within a panel"""
    antibiotic: str
    result: str # S, I, R

class ASTPanelEntry(BaseModel):
    """Request schema for manual AST Isolate Entry (Collection)"""
    lab_no: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    bht: Optional[str] = None
    ward: str
    specimen_type: str
    organism: str
    results: List[AntibioticResult] # The Collection of ABX results
    
    class Config:
        json_schema_extra = {
            "example": {
                "ward": "ICU",
                "organism": "Pseudomonas aeruginosa",
                "specimen_type": "Urine",
                "results": [
                    {"antibiotic": "Meropenem", "result": "S"},
                    {"antibiotic": "Ciprofloxacin", "result": "R"}
                ]
            }
        }

# ============================================
# Response Schemas
# ============================================

class PredictionResponse(BaseModel):
    """Response schema for prediction endpoint"""
    target_week_start: date = Field(..., description="Target week start date for prediction")
    predicted_s_percent: float = Field(..., description="Predicted susceptibility percentage")
    confidence_interval_lower: Optional[float] = Field(None, description="Lower bound of 95% confidence interval")
    confidence_interval_upper: Optional[float] = Field(None, description="Upper bound of 95% confidence interval")
    alert_level: str = Field(..., description="Traffic light alert: Green, Amber, or Red")
    model_used: str = Field(..., description="Model that generated the prediction (SMA, Prophet, ARIMA)")
    mae_score: float = Field(..., description="Mean Absolute Error of the model")
    is_ward_level: bool = Field(..., description="Whether prediction is ward-level or organism-level")
    sample_size: int = Field(..., description="Number of historical data points used")
    message: Optional[str] = Field(None, description="Additional information or warnings")
    
    class Config:
        json_schema_extra = {
            "example": {
                "target_week_start": "2025-09-01",
                "predicted_s_percent": 75.5,
                "confidence_interval_lower": 68.2,
                "confidence_interval_upper": 82.8,
                "alert_level": "Amber",
                "model_used": "Prophet",
                "mae_score": 8.3,
                "is_ward_level": True,
                "sample_size": 15,
                "message": None
            }
        }

class HistoricalDataPoint(BaseModel):
    """Single historical data point"""
    week_start_date: date
    susceptibility_percent: Optional[float]
    total_tested: int
    
class HistoricalDataResponse(BaseModel):
    """Response schema for historical data endpoint"""
    ward: Optional[str]
    organism: str
    antibiotic: str
    data_points: List[HistoricalDataPoint]
    is_ward_level: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "ward": "ICU",
                "organism": "Pseudomonas aeruginosa",
                "antibiotic": "Meropenem (MEM)",
                "is_ward_level": True,
                "data_points": [
                    {"week_start_date": "2024-01-01", "susceptibility_percent": 70.0, "total_tested": 10},
                    {"week_start_date": "2024-01-08", "susceptibility_percent": 75.5, "total_tested": 12}
                ]
            }
        }

class AvailableOption(BaseModel):
    """Single option for dropdown selection"""
    value: str
    label: str
    count: int = Field(..., description="Number of records available")

class AvailableOptionsResponse(BaseModel):
    """Response schema for available options endpoint"""
    wards: List[AvailableOption]
    organisms: List[AvailableOption]
    antibiotics: List[AvailableOption]
    
    class Config:
        json_schema_extra = {
            "example": {
                "wards": [
                    {"value": "ICU", "label": "ICU", "count": 28},
                    {"value": "02", "label": "Ward 02", "count": 25}
                ],
                "organisms": [
                    {"value": "Pseudomonas aeruginosa", "label": "Pseudomonas aeruginosa", "count": 31},
                    {"value": "Acinetobacter spp.", "label": "Acinetobacter spp.", "count": 21}
                ],
                "antibiotics": [
                    {"value": "Meropenem (MEM)", "label": "Meropenem", "count": 45},
                    {"value": "Piperacillin-Tazobactam (TZP/PTZ)", "label": "Piperacillin-Tazobactam", "count": 42}
                ]
            }
        }

class ModelPerformanceMetric(BaseModel):
    """Model performance metrics"""
    ward: Optional[str]
    organism: str
    antibiotic: str
    model_name: str
    mae_score: float
    is_best_model: bool
    training_samples: int
    trained_at: datetime

class ModelPerformanceResponse(BaseModel):
    """Response schema for model performance endpoint"""
    metrics: List[ModelPerformanceMetric]
    
    class Config:
        json_schema_extra = {
            "example": {
                "metrics": [
                    {
                        "ward": "ICU",
                        "organism": "Pseudomonas aeruginosa",
                        "antibiotic": "Meropenem (MEM)",
                        "model_name": "SMA",
                        "mae_score": 7.5,
                        "is_best_model": True,
                        "training_samples": 18,
                        "trained_at": "2025-12-30T00:00:00"
                    }
                ]
            }
        }

# ============================================
# Simple Schemas for Frontend
# ============================================

class OptionsResponse(BaseModel):
    """Simple options response for frontend"""
    wards: List[str]
    organisms: List[str]
    antibiotics: List[str]

class ModelPerformance(BaseModel):
    """Simple model performance schema"""
    model_name: str
    organism: str
    antibiotic: str
    mae_score: float
    training_samples: int
    is_best: bool

# Redefine PredictionResponse for simpler frontend use
class PredictionResponse(BaseModel):
    """Simplified prediction response"""
    prediction: float
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    alert_level: str
    model_used: str
    mae_score: Optional[float] = None
    confidence: str

# Redefine HistoricalDataPoint for simpler use
    week_start_date: str
    susceptibility_percent: float
    samples: int

# ============================================
# AUTH SCHEMAS
# ============================================
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Union[str, None] = None
    role: Union[str, None] = None

class User(BaseModel):
    username: str
    email: Union[str, None] = None
    role: str
    is_active: bool

class UserInDB(User):
    password_hash: str
