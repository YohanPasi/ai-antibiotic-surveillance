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
    model_config = {"protected_namespaces": ()}
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
    model_config = {"protected_namespaces": ()}
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
    model_config = {"extra": "ignore"}
    prediction: float
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    alert_level: str
    model_used: str
    mae_score: Optional[float] = None
    confidence: str
    message: Optional[str] = None
    is_ward_level: Optional[bool] = False
    sample_size: Optional[int] = 0



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
