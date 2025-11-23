from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..base import Base
import datetime


class StrepIsolate(Base):
    __tablename__ = "strep_isolates"

    id = Column(Integer, primary_key=True, index=True)
    sample_id = Column(String, index=True)
    patient_id = Column(String, nullable=True)
    organism = Column(String)
    sample_type = Column(String, nullable=True)
    ward = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    sex = Column(String, nullable=True)
    collection_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    ast_results = relationship("StrepAST", back_populates="isolate")


class StrepAST(Base):
    __tablename__ = "strep_ast"

    id = Column(Integer, primary_key=True, index=True)
    isolate_id = Column(Integer, ForeignKey("strep_isolates.id"))
    antibiotic = Column(String)
    result = Column(String)

    isolate = relationship("StrepIsolate", back_populates="ast_results")
