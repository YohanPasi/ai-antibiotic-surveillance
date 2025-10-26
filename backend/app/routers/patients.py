from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db.base import SessionLocal
from ..db import models
from ..schemas import schemas

router = APIRouter(prefix="/patients", tags=["Patients"])

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.Patient)
def create_patient(patient: schemas.PatientCreate, db: Session = Depends(get_db)):
    db_patient = models.Patient(**patient.dict())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

@router.get("/", response_model=list[schemas.Patient])
def get_patients(db: Session = Depends(get_db)):
    return db.query(models.Patient).all()
