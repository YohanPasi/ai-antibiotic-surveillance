from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth.routes import router as auth_router
from .routers import health, patients, mrsa
from .routers.routes_esbl import router as esbl_router

from .db.base import Base, engine
from .auth.models import User
from .db.models import Patient, Sample, ASTResult

from .config import settings

app = FastAPI(title="AI Surveillance API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(auth_router, prefix="/api")
app.include_router(mrsa.router)
app.include_router(esbl_router)
app.include_router(patients.router)
app.include_router(health.router, prefix="/api")

@app.get("/")
def root():
    return {"message": "Backend connected successfully!"}
