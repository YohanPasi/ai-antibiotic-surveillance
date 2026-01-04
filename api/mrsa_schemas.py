from pydantic import BaseModel, Field
from typing import Optional, Literal

class MRSAPredictionRequest(BaseModel):
<<<<<<< HEAD
    """
    Contract for Pre-AST MRSA Risk Assessment.
    Strictly forbids forecasting or antibiotic fields.
    """
    age: int = Field(..., ge=0, le=120)
    gender: str = Field(..., pattern="^(Male|Female|Unknown)$")
=======
    age: Optional[int] = 0
    gender: Optional[str] = "Unknown"
>>>>>>> c8d68085e364370dce8a93220bcba430401fba25
    ward: str
    sample_type: Optional[str] = "Unknown"
    pus_type: Optional[str] = "Unknown"
    cell_count: int = Field(..., ge=0, le=4, description="Ordinal 0-4")
    gram_positivity: str = Field(..., pattern="^(GPC|Unknown)$")
    growth_time: Optional[float] = Field(24.0, ge=0)
    bht: Optional[str] = "Unknown"

    class Config:
        extra = "forbid" # Reject any extra fields (safety guard)

class ModelResult(BaseModel):
    prob: float
    band: str
    version: str

class ConsensusModels(BaseModel):
    rf: ModelResult
    lr: ModelResult
    xgb: ModelResult

class ConsensusDetails(BaseModel):
    consensus_band: str
    confidence_level: str
    models: ConsensusModels
    consensus_version: str

class MRSAPredictionResponse(BaseModel):
    assessment_id: int
    mrsa_probability: float
    risk_band: Literal["GREEN", "AMBER", "RED"]
    stewardship_message: str
    model_version: str
    input_snapshot: dict
    consensus_details: Optional[ConsensusDetails] = None

class MRSAExplanationItem(BaseModel):
    feature: str
    impact: float
    value: str

class MRSAExplanationResponse(BaseModel):
    assessment_id: int
    risk_band: str
    explanations: list[MRSAExplanationItem]

# --- Master Data Schemas ---
class MasterDefinitionCreate(BaseModel):
    category: str
    label: str
    value: str

class MasterDefinitionResponse(BaseModel):
    id: int
    category: str
    label: str
    value: str
    is_active: bool

    class Config:
        from_attributes = True

# --- Stage E: Analytics & Governance Schemas ---

class MetricValue(BaseModel):
    value: float
    unit: str = "%"
    status: Literal["OK", "WARNING", "CRITICAL"]
    trend: Literal["UP", "DOWN", "STABLE"]

class SafetyMetrics(BaseModel):
    formatted_npv: MetricValue
    formatted_sensitivity: MetricValue
    false_negatives_count: int
    total_validations: int

class StewardshipMetrics(BaseModel):
    vanco_days_saved: float
    early_detection_count: int

class AnalyticsSummaryResponse(BaseModel):
    safety: SafetyMetrics
    stewardship: StewardshipMetrics
    model_health: dict # e.g. {"rf_acc": 0.85, "consensus_acc": 0.90}
    governance_status: str

class WardRiskMetric(BaseModel):
    ward: str
    red_rate: float
    total_predictions: int
    trend: str
    alert_level: str

class GovernanceDecisionCreate(BaseModel):
    triggered_by: str
    decision: Literal['MONITOR', 'RETRAIN_REVIEW', 'DISABLE_MODULE']
    notes: Optional[str] = None
