from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Patient(Base):
    __tablename__ = "patients"
    patient_id = Column(Integer, primary_key=True, index=True)
    age = Column(Integer)
    sex = Column(String(10))
    ward = Column(String(100))
    diagnosis = Column(String(255), nullable=True)
    samples = relationship("Sample", back_populates="patient")

class Sample(Base):
    __tablename__ = "samples"
    sample_id = Column(Integer, primary_key=True, index=True)
    sample_type = Column(String(50))
    collection_time = Column(DateTime)
    patient_id = Column(Integer, ForeignKey("patients.patient_id"))
    patient = relationship("Patient", back_populates="samples")
    ast_results = relationship("ASTResult", back_populates="sample")

class ASTResult(Base):
    __tablename__ = "ast_results"
    ast_id = Column(Integer, primary_key=True, index=True)
    sample_id = Column(Integer, ForeignKey("samples.sample_id"))
    organism = Column(String(120))
    antibiotic = Column(String(120))
    sir = Column(String(2))  # "S" / "I" / "R"
    sample = relationship("Sample", back_populates="ast_results")
