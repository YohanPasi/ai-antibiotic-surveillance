from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..base import Base
from datetime import datetime

class EsblIsolate(Base):
    __tablename__ = "esbl_isolates"
    sample_id = Column(Integer, primary_key=True, index=True)
    patient_key = Column(String)
    ward = Column(String)
    sample_type = Column(String)
    gram = Column(String)
    organism = Column(String)
    collection_time = Column(DateTime)
    esbl_label = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    ast = relationship("EsblAST", back_populates="isolate")
    features = relationship("EsblFeatures", back_populates="isolate")

class EsblAST(Base):
    __tablename__ = "esbl_ast"
    id = Column(Integer, primary_key=True)
    sample_id = Column(Integer, ForeignKey("esbl_isolates.sample_id"))
    antibiotic = Column(String)
    sir = Column(String)
    isolate = relationship("EsblIsolate", back_populates="ast")

class EsblFeatures(Base):
    __tablename__ = "esbl_features"
    id = Column(Integer, primary_key=True)
    sample_id = Column(Integer, ForeignKey("esbl_isolates.sample_id"))
    light_stage = Column(String)
    ward = Column(String)
    sample_type = Column(String)
    gram = Column(String)
    hour_of_day = Column(Integer)
    isolate = relationship("EsblIsolate", back_populates="features")

class EsblPrediction(Base):
    __tablename__ = "esbl_predictions"
    id = Column(Integer, primary_key=True)
    sample_id = Column(Integer, ForeignKey("esbl_isolates.sample_id"))
    light_stage = Column(String)
    esbl_proba = Column(Float)
    esbl_pred = Column(Boolean)
    version_tag = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
