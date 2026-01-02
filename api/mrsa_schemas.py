from pydantic import BaseModel
from typing import Optional

class MRSAPredictionRequest(BaseModel):
    age: Optional[int]
    gender: str
    ward: str
    sample_type: str
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
