from pydantic import BaseModel
from typing import Optional

class MRSAPredictionRequest(BaseModel):
    age: Optional[int] = 0
    gender: Optional[str] = "Unknown"
    ward: str
    sample_type: Optional[str] = "Unknown"
    pus_type: Optional[str] = "Unknown"
    cell_count: Optional[str] = "0"
    gram_positivity: Optional[str] = "Unknown"
    growth_time: Optional[float] = 0.0
    
class MRSAPredictionResponse(BaseModel):
    mrsa_probability: float
    risk_band: str
    message: str
    timestamp: str
    assessment_id: Optional[int] = None
