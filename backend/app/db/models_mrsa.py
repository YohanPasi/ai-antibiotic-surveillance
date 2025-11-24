# backend/app/db/models_mrsa.py
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from .base import Base

class MrsaIsolate(Base):
    __tablename__ = "mrsa_isolates"
    # one row per S. aureus sample
    sample_id = Column(Integer, primary_key=True, index=True)
    patient_key = Column(String(64), index=True)      # pseudo or real, stored as string
    collection_time = Column(DateTime, index=True)
    ward = Column(String(100), index=True)
    sample_type = Column(String(50))
    gram = Column(String(40))                          # e.g., "Gram-positive coccus"
    organism = Column(String(120), default="Staphylococcus aureus", index=True)

    # label if available from final report (optional)
    mrsa_label = Column(Boolean, nullable=True)        # True=MRSA, False=MSSA, None=unknown
    mecA = Column(Boolean, nullable=True)              # if present in dataset (optional)

    # relationships
    ast = relationship("MrsaAST", back_populates="isolate", cascade="all, delete-orphan")
    features = relationship("MrsaFeatures", back_populates="isolate", cascade="all, delete-orphan")
    preds = relationship("MrsaPrediction", back_populates="isolate", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_mrsa_isolates_ward_time", "ward", "collection_time"),
    )


class MrsaAST(Base):
    __tablename__ = "mrsa_ast"
    id = Column(Integer, primary_key=True)
    sample_id = Column(Integer, ForeignKey("mrsa_isolates.sample_id", ondelete="CASCADE"), index=True)
    antibiotic = Column(String(80), index=True)        # e.g., "Cefoxitin"
    sir = Column(String(2))                             # "S"/"I"/"R"

    isolate = relationship("MrsaIsolate", back_populates="ast")

    __table_args__ = (
        UniqueConstraint("sample_id", "antibiotic", name="uq_mrsa_ast_sample_abx"),
    )


class MrsaFeatures(Base):
    __tablename__ = "mrsa_features"
    id = Column(Integer, primary_key=True)
    sample_id = Column(Integer, ForeignKey("mrsa_isolates.sample_id", ondelete="CASCADE"), index=True)
    # “traffic light” feature snapshots
    light_stage = Column(String(16), index=True)       # "light1", "light4", etc.

    # minimal common predictors (extend as you need)
    ward = Column(String(100))
    sample_type = Column(String(50))
    gram = Column(String(40))
    # you can add engineered features too (hour_of_day, ward_prev_24h_staph, etc.)
    hour_of_day = Column(Integer, nullable=True)

    isolate = relationship("MrsaIsolate", back_populates="features")

    __table_args__ = (
        UniqueConstraint("sample_id", "light_stage", name="uq_mrsa_feat_sample_stage"),
    )


class MrsaPrediction(Base):
    __tablename__ = "mrsa_predictions"
    id = Column(Integer, primary_key=True)
    sample_id = Column(Integer, ForeignKey("mrsa_isolates.sample_id", ondelete="CASCADE"), index=True, nullable=True)

    # Metadata fields (for compatibility with prediction router)
    ward = Column(String(100), nullable=True)
    sample_type = Column(String(50), nullable=True)
    organism = Column(String(120), nullable=True)
    gram = Column(String(40), nullable=True)

    # Model information
    model_name = Column(String(120), nullable=True)    # e.g., "lightgbm_v1"
    model_type = Column(String(40), nullable=True)     # e.g., "light1", "light4" (for compatibility)
    model_version = Column(String(40), nullable=True) # e.g., "2025.10.27"
    created_at = Column(DateTime)

    # Prediction outputs
    probability = Column(Float, nullable=True)         # probability of MRSA (for compatibility)
    predicted_label = Column(Integer, nullable=True)   # 0 or 1 (for compatibility)
    p_mrsa = Column(Float, nullable=True)              # probability of MRSA at current stage
    p_vanc_effective = Column(Float, nullable=True)    # optional per-drug predictions
    p_cefoxitin_effective = Column(Float, nullable=True)

    isolate = relationship("MrsaIsolate", back_populates="preds")

    __table_args__ = (
        Index("ix_mrsa_preds_model_time", "model_name", "created_at"),
    )
