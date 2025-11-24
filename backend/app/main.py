from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .auth.routes import router as auth_router
from .routers import health, patients, mrsa
from .routers.routes_esbl import router as esbl_router
from .routers.nonfermenter import router as nonfermenter_router
from .routers.strep import router as strep_router

from .db.base import Base, engine
from .auth.models import User
from .db.models import Patient, Sample, ASTResult
from .db.models_mrsa import MrsaIsolate, MrsaAST, MrsaFeatures, MrsaPrediction
from app.routers import mrsa_predict, mrsa_dashboard



from .config import settings

app = FastAPI(title="AI Surveillance API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler to ensure CORS headers are always included
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    error_detail = str(exc)
    traceback_str = traceback.format_exc()
    print(f"Error: {error_detail}\n{traceback_str}")  # Log to console
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": error_detail, "error": "Internal server error"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
        }
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
        }
    )

Base.metadata.create_all(bind=engine)

app.include_router(auth_router, prefix="/api")
app.include_router(mrsa.router)
app.include_router(esbl_router)
app.include_router(patients.router)
app.include_router(health.router, prefix="/api")
app.include_router(nonfermenter_router)
app.include_router(strep_router)
app.include_router(mrsa_predict.router)
app.include_router(mrsa_dashboard.router)


@app.get("/")
def root():
    return {"message": "Backend connected successfully!"}
