from fastapi import FastAPI
from app.routers import patients
from fastapi.middleware.cors import CORSMiddleware

# Import Base and engine
from .db.base import Base, engine

# ⚠️ Import models so SQLAlchemy "sees" them before create_all
from .db.models import Patient, Sample, ASTResult

from .config import settings
from .routers import health

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
app.include_router(patients.router)

@app.get("/")
def root():
    return {"message": "Backend connected successfully!"}
