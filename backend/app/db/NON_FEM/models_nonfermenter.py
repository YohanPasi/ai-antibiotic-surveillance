from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class NonFermenterIsolate(Base):
    __tablename__ = "nonfermenter_isolates"

    id = Column(Integer, primary_key=True, index=True)
    sample_id = Column(String, index=True)
    patient_id = Column(String, nullable=True)
    organism = Column(String)
    ward = Column(String, nullable=True)
    sample_type = Column(String, nullable=True)
    collection_time = Column(DateTime, nullable=True)
    gram = Column(String, nullable=True)

    # Antibiotics
    meropenem = Column(String, nullable=True)
    imipenem = Column(String, nullable=True)
    ceftazidime = Column(String, nullable=True)
    cefepime = Column(String, nullable=True)
    amikacin = Column(String, nullable=True)
    gentamicin = Column(String, nullable=True)
    tobramycin = Column(String, nullable=True)
    ciprofloxacin = Column(String, nullable=True)
    colistin = Column(String, nullable=True)

    # 1 = Carbapenem Resistant
    carbapenem_resistant = Column(Integer)

    # Relationship
    ast = relationship("NonFermenterAST", back_populates="isolate")
    features = relationship("NonFermenterFeature", back_populates="isolate")


class NonFermenterAST(Base):
    __tablename__ = "nonfermenter_ast"

    id = Column(Integer, primary_key=True, index=True)
    isolate_id = Column(Integer, ForeignKey("nonfermenter_isolates.id", ondelete="CASCADE"), index=True)
    antibiotic = Column(String)
    sir = Column(String)

    isolate = relationship("NonFermenterIsolate", back_populates="ast")


class NonFermenterFeature(Base):
    __tablename__ = "nonfermenter_features"

    id = Column(Integer, primary_key=True, index=True)
    isolate_id = Column(Integer, ForeignKey("nonfermenter_isolates.id", ondelete="CASCADE"), index=True)
    light_stage = Column(String)
    ward = Column(String, nullable=True)
    sample_type = Column(String, nullable=True)
    gram = Column(String, nullable=True)
    hour_of_day = Column(Integer, nullable=True)

    isolate = relationship("NonFermenterIsolate", back_populates="features")
