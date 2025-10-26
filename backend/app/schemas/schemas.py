from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

# ---------- AST Result ----------
class ASTResultBase(BaseModel):
    organism: str
    antibiotic: str
    sir: str

class ASTResultCreate(ASTResultBase):
    sample_id: int

class ASTResult(ASTResultBase):
    ast_id: int

    class Config:
        orm_mode = True


# ---------- Sample ----------
class SampleBase(BaseModel):
    sample_type: str
    collection_time: datetime

class SampleCreate(SampleBase):
    patient_id: int

class Sample(SampleBase):
    sample_id: int
    ast_results: List[ASTResult] = []

    class Config:
        orm_mode = True


# ---------- Patient ----------
class PatientBase(BaseModel):
    age: int
    sex: str
    ward: str
    diagnosis: Optional[str] = None

class PatientCreate(PatientBase):
    pass

class Patient(PatientBase):
    patient_id: int
    samples: List[Sample] = []

    class Config:
        orm_mode = True
