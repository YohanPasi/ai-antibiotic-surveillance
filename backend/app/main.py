from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import Base and engine
from .db.base import Base, engine

# ⚠️ Import models so SQLAlchemy "sees" them before create_all
from .db.models import Patient, Sample, ASTResult
from .db.ESBL.models_esbl import EsblIsolate, EsblAST, EsblFeatures, EsblPrediction

from .config import settings
from .routers import health, patients, mrsa, routes_esbl

app = FastAPI(title="AI Antibiotic Surveillance API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables now that models are imported
Base.metadata.create_all(bind=engine)

app.include_router(health.router, prefix="/api")
app.include_router(mrsa.router)
app.include_router(patients.router)
app.include_router(routes_esbl.router)

@app.get("/")
def root():
    return {"message": "Backend connected successfully!"}
