from pydantic import BaseModel, Field
from typing import Optional, Literal


class MRSAPredictionRequest(BaseModel):
    """
    MRSA Pre-AST Risk Screening Request — Schema v2.
    Aligned with canonical feature set defined in docs/mrsa_features.md.
    Deprecated fields (age, gender, pus_type, cell_count, gram_positivity) are removed.
    """
    ward: str

    sample_type: str

    gram_stain: str = Field(
        ...,
        pattern="^(GPC|Unknown)$",
        description="Gram stain result. GPC = Gram-positive cocci."
    )

    cell_count_category: str = Field(
        ...,
        pattern="^(LOW|MEDIUM|HIGH)$",
        description="Pus cell count: LOW (<10/HPF), MEDIUM (10-25/HPF), HIGH (>25/HPF)"
    )

    growth_time: Optional[float] = Field(
        None,
        ge=0,
        description="Blood culture growth time in hours. NULL for non-blood samples."
    )

    recent_antibiotic_use: str = Field(
        ...,
        pattern="^(Yes|No|Unknown)$",
        description="Whether the patient received antibiotics in the last 14 days."
    )

    length_of_stay: int = Field(
        ...,
        ge=0,
        description="Number of days the patient has been admitted."
    )

    # Record-keeping only — must never enter the model feature vector
    bht: Optional[str] = None

    class Config:
        extra = "forbid"  # Hard reject any field not listed above


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
    model_health: dict  # e.g. {"rf_acc": 0.85, "consensus_acc": 0.90}
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
