"""
FastAPI main application
AST Prediction & Surveillance System
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import logging
import json

from database import SessionLocal, test_connection
from sqlalchemy import text
from schemas import (
    PredictionRequest,
    PredictionResponse,
    HistoricalDataResponse,
    AvailableOptionsResponse,
    ModelPerformanceResponse,
    HistoricalDataPoint,
    OptionsResponse,
    ModelPerformance,
    ASTPanelEntry,
    Token,
    User,
    UserInDB
)
from mrsa_schemas import MRSAPredictionRequest, MRSAPredictionResponse, MRSAExplanationResponse
from mrsa_schemas import MRSAPredictionRequest, MRSAPredictionResponse, MRSAExplanationResponse, MasterDefinitionCreate, MasterDefinitionResponse
from mrsa_service import mrsa_service
from master_data_service import MasterDataService
from prediction_service import PredictionService
import statistics
import numpy as np
from fastapi.security import OAuth2PasswordRequestForm

# Auth Logic
import auth
from auth import User, get_current_user


# Startup Logic
from startup_manager import StartupManager

# Stage 2 Router
from routers import stp_stage_2, stp_stage_3, stp_stage_4, stp_stage_5, stp_overview, stp_feedback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AST Prediction API",
    description="AI-Driven Antibiotic Susceptibility Testing Prediction System for Non-Fermenters",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS (Must be added immediately after app creation)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "http://localhost:8080"
    ], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Stage 2 Router (Read-Only)
app.include_router(stp_stage_2.router)
app.include_router(stp_stage_3.router)
app.include_router(stp_stage_4.router)
app.include_router(stp_stage_5.router)
app.include_router(stp_overview.router)
app.include_router(stp_feedback.router)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================
# AUTHENTICATION ENDPOINTS
# ============================================
@app.post("/api/auth/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    db = SessionLocal()
    try:
        user_query = text("SELECT username, password_hash, role, is_active FROM users WHERE username = :username")
        user = db.execute(user_query, {"username": form_data.username}).fetchone()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        if not auth.verify_password(form_data.password, user[1]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        if not user[3]: # is_active
            raise HTTPException(status_code=400, detail="Inactive user")

        access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth.create_access_token(
            data={"sub": user[0], "role": user[2]}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    finally:
        db.close()

@app.get("/api/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.post("/api/auth/register", response_model=User)
async def register_user(new_user: User): # Using User schema for input for simplicity + password logic internally? No, need schema with password.  
    # Ideally should use a UserCreate schema. For now, let's keep it simple or update schema.
    # Actually, let's just use JSON body for now
    pass 
    # NOTE: Registration is manually disabled for this phase to enforce "Seed Admin Only".
    # User requested login/permissions, not necessarily open registration.
    raise HTTPException(status_code=403, detail="Registration is disabled. Contact Admin.")

# ============================================
# Health Check Endpoints
# ============================================
from fastapi import status

@app.get("/")
async def root():
    """Root endpoint - API status"""
    return {
        "message": "AST Prediction API is running",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_status = test_connection()
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected"
    }

# ============================================
# Background Tasks (Pipeline Automation)
# ============================================
import subprocess
import asyncio
from fastapi import BackgroundTasks

def trigger_pipeline_update():
    """
    Executes the Data Pipeline automations:
    1. Stage B: Aggregate Weekly (Updates ast_weekly_aggregated)
    2. Stage E: Continuous Learning (Validates & Forecasts)
    """
    try:
        logger.info("⚙️ Triggering Background Pipeline Update...")
        
        # 1. Run Aggregation
        # Note: In production this should be a celery task or direct function call.
        # For this setup, we invoke the script.
        logger.info("   Running Stage B: Aggregation...")
        subprocess.run(["python", "/app/data_processor/aggregate_weekly.py"], check=True)
        
        # 2. Run Stage E
        logger.info("   Running Stage E: Continuous Learning...")
        subprocess.run(["python", "/app/cron/stage_e_continuous_learning.py"], check=True)
        
        logger.info("✅ Pipeline Update Completed Successfully")
    except Exception as e:
        logger.error(f"❌ Pipeline Update Failed: {e}")

# ============================================
# In-Process Surveillance Sweep
# ============================================

def run_surveillance_sweep():
    """
    Runs LSTM+SMA hybrid predictions for ALL (ward, organism, antibiotic)
    combinations in ast_weekly_aggregated and writes to surveillance_logs.
    Covers all organisms — Pseudomonas, Acinetobacter, Staphylococcus, etc.
    """
    db = SessionLocal()
    try:
        logger.info("🏥 Starting In-Process Surveillance Sweep for ALL organisms...")
        # Get Ward-specific targets
        targets_ward = db.execute(text("""
            SELECT DISTINCT ward, organism, antibiotic
            FROM ast_weekly_aggregated
            WHERE total_tested >= 3
        """)).fetchall()

        # Get Hospital-Wide targets
        targets_hw = db.execute(text("""
            SELECT DISTINCT NULL as ward, organism, antibiotic
            FROM ast_weekly_aggregated
            WHERE total_tested >= 3
        """)).fetchall()

        targets = targets_ward + targets_hw
        logger.info(f"   Found {len(targets_ward)} Ward and {len(targets_hw)} Hospital-Wide targets")

        success_count = 0
        skip_count = 0

        for ward, organism, antibiotic in targets:
            try:
                if ward is not None:
                    rows = db.execute(text("""
                        SELECT susceptibility_percent
                        FROM ast_weekly_aggregated
                        WHERE organism = :organism AND antibiotic = :antibiotic
                          AND ward = :ward AND total_tested >= 3
                        ORDER BY week_start_date DESC LIMIT 5
                    """), {"organism": organism, "antibiotic": antibiotic, "ward": ward}).fetchall()
                else:
                    rows = db.execute(text("""
                        SELECT ROUND((SUM(susceptible_count)::NUMERIC / SUM(total_tested)::NUMERIC) * 100, 2)
                        FROM ast_weekly_aggregated
                        WHERE organism = :organism AND antibiotic = :antibiotic
                        GROUP BY week_start_date
                        HAVING SUM(total_tested) >= 3
                        ORDER BY week_start_date DESC LIMIT 5
                    """), {"organism": organism, "antibiotic": antibiotic}).fetchall()

                history_data = [float(r[0]) for r in rows if r[0] is not None]
                if not history_data:
                    skip_count += 1
                    continue

                observed_s = history_data[0]
                past_history = history_data[1:]

                if len(past_history) < 2:
                    baseline_mean = statistics.mean(history_data)
                    baseline_lower = baseline_mean - 10.0
                else:
                    baseline_mean = statistics.mean(past_history)
                    baseline_std = statistics.stdev(past_history)
                    baseline_lower = baseline_mean - (1.5 * baseline_std)
                baseline_lower = max(0, min(100, baseline_lower))

                lstm_model = getattr(app.state, 'lstm_model', None)
                lstm_forecast = PredictionService.predict_with_lstm(lstm_model, past_history[::-1]) if lstm_model else baseline_mean

                if ward is not None:
                    prev_statuses = [r[0] for r in db.execute(text("""
                        SELECT alert_status FROM surveillance_logs
                        WHERE ward = :ward AND organism = :organism AND antibiotic = :antibiotic
                        ORDER BY log_date DESC LIMIT 3
                    """), {"ward": ward, "organism": organism, "antibiotic": antibiotic}).fetchall()]
                else:
                    prev_statuses = [r[0] for r in db.execute(text("""
                        SELECT alert_status FROM surveillance_logs
                        WHERE ward IS NULL AND organism = :organism AND antibiotic = :antibiotic
                        ORDER BY log_date DESC LIMIT 3
                    """), {"organism": organism, "antibiotic": antibiotic}).fetchall()]

                status, direction, reason = PredictionService.get_hybrid_status(
                    observed_s, baseline_lower, lstm_forecast, prev_statuses
                )
                prompt, domain = PredictionService.generate_detailed_stewardship(
                    status, organism, antibiotic, ward if ward else "Hospital-Wide"
                )

                db.execute(text("""
                    INSERT INTO surveillance_logs (
                        week_start_date, ward, organism, antibiotic,
                        observed_s_percent, predicted_s_percent, baseline_s_percent, baseline_lower_bound,
                        forecast_deviation, alert_status, previous_alert_status, alert_reason,
                        stewardship_prompt, stewardship_domain, model_version, consensus_path
                    ) VALUES (
                        CURRENT_DATE, :ward, :org, :abx,
                        :obs, :pred, :base, :base_lower,
                        :dev, :status, :prev_status, :reason,
                        :prompt, :domain, 'LSTM_v1_Hybrid', 'Sweep_Automated_V2'
                    )
                """), {
                    "ward": ward, "org": organism, "abx": antibiotic,
                    "obs": observed_s, "pred": lstm_forecast,
                    "base": baseline_mean, "base_lower": baseline_lower,
                    "dev": lstm_forecast - baseline_mean,
                    "status": status,
                    "prev_status": prev_statuses[0] if prev_statuses else None,
                    "reason": reason, "prompt": prompt, "domain": domain
                })
                success_count += 1

            except Exception as target_err:
                db.rollback()
                logger.warning(f"   ⚠️ Sweep skipped {ward}/{organism}/{antibiotic}: {target_err}")
                skip_count += 1
                continue

        db.commit()
        logger.info(f"✅ Surveillance Sweep Complete — {success_count} logged, {skip_count} skipped")
        return {"success": success_count, "skipped": skip_count}

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Surveillance Sweep Failed: {e}")
        return {"error": str(e)}
    finally:
        db.close()


@app.on_event("startup")
async def on_startup():
    """
    On API startup: trigger a background sweep if surveillance_logs is
    smaller than ast_weekly_aggregated (i.e. new organisms have no AI log yet).
    """
    db = SessionLocal()
    try:
        log_count = db.execute(text("SELECT COUNT(*) FROM surveillance_logs")).scalar()
        agg_count = db.execute(text("SELECT COUNT(DISTINCT ward || organism || antibiotic) FROM ast_weekly_aggregated")).scalar()
        if agg_count > 0 and log_count < agg_count:
            logger.info("🚀 Startup: surveillance_logs incomplete — running background sweep...")
            import threading
            threading.Thread(target=run_surveillance_sweep, daemon=True).start()
        else:
            logger.info(f"✅ Startup: {log_count} log entries — sweep not needed")
    except Exception as e:
        logger.warning(f"Startup sweep check (non-critical): {e}")
    finally:
        db.close()


# ============================================
# API Endpoints
# ============================================

@app.post("/api/admin/sweep")
async def trigger_surveillance_sweep(background_tasks: BackgroundTasks):
    """
    Manually trigger a full hospital-wide LSTM surveillance sweep for ALL organisms.
    Populates surveillance_logs with AI Forecast predictions for every
    (ward, organism, antibiotic) combination including Staphylococcus aureus.
    """
    background_tasks.add_task(run_surveillance_sweep)
    return {
        "status": "triggered",
        "message": "Full surveillance sweep started. Refresh the antibiogram in ~15 seconds."
    }


import asyncio

async def trigger_nf_pipeline():
    """
    Executes the Phase 2 Non-Fermenter Controlled Sequence:
    1. Stage B: Full Aggregation
    2. Stage C: Baseline Recompute
    3. Sweep: Prediction Engine
    """
    try:
        import subprocess
        # Wait 2 seconds for the synchronous SQLAlchemy connection pooling 
        # to fully release row-exclusive locks on PostgreSQL.
        await asyncio.sleep(2)
        
        logger.info("⚙️ Triggering Phase 2 NF Surveillance Pipeline...")
        logger.info("   1. Running Stage B: Aggregation...")
        subprocess.run(["python", "/app/data_processor/aggregate_weekly.py"], check=True)
        logger.info("   2. Running Stage C: Baseline Recompute...")
        subprocess.run(["python", "/app/data_processor/compute_baselines.py"], check=True)
        logger.info("   3. Running Sweep: Prediction Engine...")
        run_surveillance_sweep()
        logger.info("✅ NF Pipeline Completed Successfully")
    except Exception as e:
        logger.error(f"NF Pipeline Error: {e}")

@app.post("/api/entry")
async def create_ast_entry(entry: ASTPanelEntry, background_tasks: BackgroundTasks):
    """
    Manual AST Data Entry Endpoint (Panel/Collection).
    Saves raw data and triggers the correctly sequenced Learning Loop.
    """
    db = SessionLocal()
    try:
        culture_date_val = entry.culture_date or datetime.now().date()
        
        # Backend Guard: Reject Future Dates (Data Integrity)
        if culture_date_val > datetime.now().date():
            raise HTTPException(status_code=400, detail="Future culture date not allowed")

        # 1. SQL Query
        query = text("""
            INSERT INTO ast_manual_entry (
                culture_date, lab_no, age, gender, bht, ward, specimen_type, organism, antibiotic, result
            ) VALUES (
                :cd, :lab, :age, :gen, :bht, :ward, :spec, :org, :abx, :res
            )
        """)
        
        # 2. Iterate Collection and Insert
        for item in entry.results:
            db.execute(query, {
                "cd": culture_date_val,
                "lab": entry.lab_no, "age": entry.age, "gen": entry.gender,
                "bht": entry.bht, "ward": entry.ward, "spec": entry.specimen_type,
                "org": entry.organism, "abx": item.antibiotic, "res": item.result
            })
            
        # 3. TRIGGER MRSA VALIDATION (Stage D)
        # Hook: Validate prediction against Ground Truth if S. aureus
        if entry.organism == "Staphylococcus aureus":
            try:
                from mrsa_validation_service import mrsa_validation_service
                mrsa_validation_service.validate(db, entry)
            except Exception as val_err:
                logger.error(f"Validation Trigger Error: {val_err}")

        # Explicit Commit to avoid race conditions with aggregate rebuild
        db.commit()
        
        # 4. Trigger Background Controlled Sequence
        if entry.organism in ('Pseudomonas aeruginosa', 'Acinetobacter baumannii'):
            background_tasks.add_task(trigger_nf_pipeline)
        else:
            background_tasks.add_task(trigger_pipeline_update)
        
        return {"status": "success", "message": f"Panel saved ({len(entry.results)} results). Execution Pipeline triggered."}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Entry Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

# Scope lock: Non-Fermenters only
NF_ORGANISMS_SQL = "('Pseudomonas aeruginosa', 'Acinetobacter baumannii')"

@app.get("/api/options", response_model=OptionsResponse)
async def get_available_options():
    """
    Get available filter options (wards, organisms, antibiotics).
    Non-Fermenter module: only Pseudomonas aeruginosa and Acinetobacter baumannii.
    """
    try:
        db = SessionLocal()
        
        # Wards that have NF data only
        wards_query = """
            SELECT DISTINCT ward FROM ast_weekly_aggregated 
            WHERE ward IS NOT NULL
              AND organism IN ('Pseudomonas aeruginosa', 'Acinetobacter baumannii')
            ORDER BY ward
        """
        # Strict NF organism list
        organisms_query = """
            SELECT DISTINCT organism FROM ast_weekly_aggregated 
            WHERE organism IN ('Pseudomonas aeruginosa', 'Acinetobacter baumannii')
            ORDER BY organism
        """
        # Only antibiotics that appear for NF organisms
        antibiotics_query = """
            SELECT DISTINCT antibiotic FROM ast_weekly_aggregated 
            WHERE organism IN ('Pseudomonas aeruginosa', 'Acinetobacter baumannii')
            ORDER BY antibiotic
        """
        
        wards = [row[0] for row in db.execute(text(wards_query)).fetchall()]
        organisms = [row[0] for row in db.execute(text(organisms_query)).fetchall()]
        antibiotics = [row[0] for row in db.execute(text(antibiotics_query)).fetchall()]
        
        db.close()
        
        return OptionsResponse(
            wards=wards if wards else ["ICU", "Ward A", "Ward B"],
            organisms=organisms if organisms else ["Pseudomonas aeruginosa", "Acinetobacter baumannii"],
            antibiotics=antibiotics if antibiotics else ["Meropenem", "Ceftazidime", "Ciprofloxacin"]
        )
    except Exception as e:
        logger.error(f"Error getting options: {e}")
        # Return demo data on error
        return OptionsResponse(
            wards=["ICU", "Medical Ward", "Surgical Ward"],
            organisms=["Pseudomonas aeruginosa", "Acinetobacter spp."],
            antibiotics=["Meropenem", "Ceftazidime", "Amikacin"]
        )

@app.get("/api/historical")
async def get_historical_data(
    organism: str,
    antibiotic: str,
    ward: Optional[str] = None
):
    """
    Get historical weekly S% data for time series visualization.
    """
    try:
        db = SessionLocal()
        
        if ward:
            # Ward-specific data
            query = """
                SELECT week_start_date, susceptibility_percent, total_tested
                FROM ast_weekly_aggregated
                WHERE organism = :organism
                  AND antibiotic = :antibiotic
                  AND ward = :ward
                  AND total_tested >= 3  -- Methodological 'Minimum Isolate Rule'
                ORDER BY week_start_date
            """
            result = db.execute(text(query), {"organism": organism, "antibiotic": antibiotic, "ward": ward})
        else:
            # Organism-level data
            query = """
                SELECT week_start_date, susceptibility_percent, total_tested
                FROM organism_level_aggregation
                WHERE organism = :organism
                  AND antibiotic = :antibiotic
                  AND total_tested >= 3 -- Methodological 'Minimum Isolate Rule'
                ORDER BY week_start_date
            """
            result = db.execute(text(query), {"organism": organism, "antibiotic": antibiotic})
        
        rows = result.fetchall()
        db.close()
        
        historical_data = [
            HistoricalDataPoint(
                week_start_date=str(row[0]),
                susceptibility_percent=float(row[1]),
                samples=int(row[2])
            )
            for row in rows
        ]
        
        return {"data": historical_data, "count": len(historical_data)}
            
    except Exception as e:
        logger.error(f"Error getting historical data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/predict", response_model=PredictionResponse)
async def get_prediction(request: PredictionRequest):
    """
    Generate next week's S% prediction using HYBRID SURVEILLANCE ENGINE.
    1. Statistical Baseline (Holt-Winters/SMA from History)
    2. Deep Learning Forecast (LSTM)
    3. Consensus Alerting (Green/Amber/Red)
    """
    logger.info(f"🔮 HYBRID SURVEILLANCE REQUEST: {request.organism} | {request.antibiotic} | Ward: {request.ward}")
    
    db = SessionLocal()
    
    try:
        # STEP 1: Fetch Real Historical Data (Last 5 weeks)
        # We need Week 0 (Current Observed) and Weeks -1 to -4 (History for LSTM)
        query = """
            SELECT susceptibility_percent
            FROM ast_weekly_aggregated
            WHERE organism = :organism
              AND antibiotic = :antibiotic
              AND (:ward IS NULL OR ward = :ward)
              AND total_tested >= 3
            ORDER BY week_start_date DESC
            LIMIT 5
        """
        result = db.execute(text(query), {
            "organism": request.organism,
            "antibiotic": request.antibiotic,
            "ward": request.ward
        }).fetchall()
        
        # Flatten results
        history_data = [float(row[0]) for row in result]
        
        # Check if we have enough data for a valid surveillance signal
        # We need at least the current week (observed) and some history
        if len(history_data) >= 1:
            # We have real data!
            observed_s = history_data[0] # Most recent week
            past_history = history_data[1:] # Previous weeks
            
            # Use whole history for statistics if recent history is short, 
            # or use last 4 points. 
            # Ideally we'd fetch more for a robust baseline, but for this demo 5 points is okay.
            # Let's assume baseline calculation uses the provided history.
            
            # STEP 2: Statistical Baseline
            if len(past_history) < 2:
                baseline_mean = statistics.mean(history_data)
                baseline_lower = baseline_mean - 10.0 
            else:
                baseline_mean = statistics.mean(past_history)
                baseline_std = statistics.stdev(past_history)
                baseline_lower = baseline_mean - (1.5 * baseline_std)
                
            baseline_lower = max(0, min(100, baseline_lower))
            
            # STEP 3: Deep Learning Forecast
            lstm_model = app.state.lstm_model
            lstm_forecast = 0.0
            
            if lstm_model:
                lstm_input = past_history[::-1] 
                lstm_forecast = PredictionService.predict_with_lstm(lstm_model, lstm_input)
                logger.info(f"🧠 LSTM Forecast: {lstm_forecast:.2f}% (Observed: {observed_s:.2f}%)")
            else:
                lstm_forecast = baseline_mean 

            # STEP 3.5: Fetch Persistence History (Operational Intelligence)
            prev_status_query = """
                SELECT alert_status FROM surveillance_logs 
                WHERE ward = :ward AND organism = :organism AND antibiotic = :antibiotic 
                ORDER BY log_date DESC LIMIT 3
            """
            prev_statuses = [row[0] for row in db.execute(text(prev_status_query), {
                "ward": request.ward, "organism": request.organism, "antibiotic": request.antibiotic
            }).fetchall()]

            # STEP 4: Consensus Alert Logic (Hybrid + Persistence)
            status, direction, reason = PredictionService.get_hybrid_status(
                observed_s, baseline_lower, lstm_forecast, prev_statuses
            )
            
            # STEP 5: Context-Aware Stewardship
            prompt, domain = PredictionService.generate_detailed_stewardship(
                status, request.organism, request.antibiotic, request.ward
            )
            
            # STEP 6: Audit Logging (Traceability)
            forecast_deviation = lstm_forecast - baseline_mean
            
            log_query = """
                INSERT INTO surveillance_logs (
                    week_start_date, ward, organism, antibiotic,
                    observed_s_percent, predicted_s_percent, baseline_s_percent, baseline_lower_bound,
                    forecast_deviation, alert_status, previous_alert_status, alert_reason,
                    stewardship_prompt, stewardship_domain, 
                    model_version, consensus_path
                ) VALUES (
                    CURRENT_DATE, :ward, :org, :abx,
                    :obs, :pred, :base, :base_lower,
                    :dev, :status, :prev_status, :reason,
                    :prompt, :domain,
                    'LSTM_v1_Hybrid', 'Automated Consensus V2'
                )
            """
            
            try:
                db.execute(text(log_query), {
                    "ward": request.ward, "org": request.organism, "abx": request.antibiotic,
                    "obs": observed_s, "pred": lstm_forecast, "base": baseline_mean, "base_lower": baseline_lower,
                    "dev": forecast_deviation, "status": status, 
                    "prev_status": prev_statuses[0] if prev_statuses else None,
                    "reason": reason, "prompt": prompt, "domain": domain
                })
                db.commit()
                logger.info("📝 Audit Log saved.")
            except Exception as log_err:
                logger.error(f"Failed to save audit log: {log_err}")

            logger.info(f"🚦 Final Status: {status.upper()} | {direction} | Reason: {reason}")
            
            return PredictionResponse(
                prediction=round(lstm_forecast, 2),
                lower_bound=round(baseline_lower, 2),
                upper_bound=100.0,
                alert_level=status,
                model_used="Hybrid (LSTM + Persistence)",
                mae_score=0.00,
                confidence="High",
                is_ward_level=True if request.ward else False,
                sample_size=len(history_data) * 10,
                message=f"[{domain}] {prompt} (Reason: {reason})"
            )

        else:
            # Not enough data -> Demo Mode (Fallback)
            logger.warning("ℹ️ Insufficient Data for Hybrid Logic (>3 weeks needed). Falling back to Demo.")
            demo = PredictionService.generate_demo_prediction(request.organism, request.antibiotic)
            demo['message'] = "Note: Insufficient historical data for this specific Ward/Bug combination. Showing Demo values."
            return PredictionResponse(**demo)
            
    except Exception as e:
        logger.error(f"🔥 CRITICAL ERROR in predict endpoint: {e}")
        demo = PredictionService.generate_demo_prediction(request.organism, request.antibiotic)
        demo['message'] = f"System Error: {str(e)}"
        return PredictionResponse(**demo)
    finally:
        db.close()


@app.get("/api/model-performance")
async def get_model_performance(
    organism: Optional[str] = None,
    antibiotic: Optional[str] = None
):
    """
    Get model performance comparison data.
    """
    try:
        db = SessionLocal()
        
        query = """
            SELECT model_name, organism, antibiotic, mae_score, 
                   training_samples, is_best_model
            FROM model_performance
            WHERE 1=1
        """
        
        params = {}
        if organism:
            query += " AND organism = :organism"
            params["organism"] = organism
        if antibiotic:
            query += " AND antibiotic = :antibiotic"
            params["antibiotic"] = antibiotic
        
        query += " ORDER BY organism, antibiotic, mae_score ASC"
        
        result = db.execute(text(query), params)
        rows = result.fetchall()
        db.close()
        
        models = [
            ModelPerformance(
                model_name=row[0],
                organism=row[1],
                antibiotic=row[2],
                mae_score=round(float(row[3]), 2),
                training_samples=int(row[4]),
                is_best=bool(row[5])
            )
            for row in rows
        ]
        
        return {"models": models, "count": len(models)}
        
    except Exception as e:
        logger.error(f"Error getting model performance: {e}")
        # Return empty list on error
        return {"models": [], "count": 0}

@app.get("/api/analysis/target")
async def get_target_analysis(ward: str, organism: str, antibiotic: str):
    """
    Detailed Analysis Endpoint for Visualization.
    Returns: History, Baseline, and ONE Forecast point.
    """
    db = SessionLocal()
    try:
        # 1. Fetch History — most recent 12 weeks, then reverse for ASC chart display
        query = """
            SELECT week_start_date, susceptible_count, total_tested
            FROM ast_weekly_aggregated
            WHERE ward = :ward AND organism = :organism AND antibiotic = :antibiotic
            ORDER BY week_start_date DESC
            LIMIT 12
        """
        results = db.execute(text(query), {
            "ward": ward, "organism": organism, "antibiotic": antibiotic
        }).fetchall()

        # Reverse so chart renders oldest → newest left to right
        results = list(reversed(results))

        # 1b. Fetch the true last signal date independently — never rely on list ordering
        anchor_query = """
            SELECT MAX(week_start_date)
            FROM ast_weekly_aggregated
            WHERE ward = :ward AND organism = :organism AND antibiotic = :antibiotic
        """
        anchor_row = db.execute(text(anchor_query), {
            "ward": ward, "organism": organism, "antibiotic": antibiotic
        }).fetchone()
        true_last_date = anchor_row[0] if anchor_row and anchor_row[0] else None

        history = []
        s_values = []

        for row in results:
            total = row[2]
            s_percent = (row[1] / total * 100.0) if total > 0 else 0.0
            history.append({
                "week": row[0].strftime("%Y-W%U"),
                "date": row[0].strftime("%b %d"),
                "week_start_date": row[0].isoformat(),  # ISO string for frontend stale detection
                "observed_s": round(s_percent, 1)
            })
            s_values.append(s_percent)
            
        # 2. Compute Baseline (Simple Moving Average - 4 weeks)
        baseline = []
        for i in range(len(history)):
            # Window of up to 4 previous weeks including current
            window = s_values[max(0, i-3):i+1]
            avg = sum(window) / len(window) if window else 0
            baseline.append({
                "week": history[i]["week"],
                "expected_s": round(avg, 1)
            })
            
        # ── Safe defaults for model-performance locals (set inside if block below) ──
        # These must be initialised here so the return-dict enrichment is always valid
        # regardless of whether the if len(s_values) >= 3 branch runs.
        observed_s        = s_values[-1] if s_values else None
        baseline_val      = baseline[-1]["expected_s"] if baseline else (s_values[-1] if s_values else None)
        adaptive_tolerance = 10.0
        rolling_mae_4c    = None
        mean_bias_4c      = None
        degraded_4c       = False
        validated_count_4b = 0
        active_model_4b   = "BASELINE_MEAN"
        pred_value        = s_values[-1] if s_values else 0.0
        drift_analysis    = {}

        # 3. Generate ONE Forecast Point
        # We need the last 4 weeks of data for the LSTM
        forecast = None
        status = "GREEN" # Default
        domain = "Routine Monitoring"
        
        if len(s_values) >= 3: # Minimum for decent prediction
             # Prepare input for LSTM
             recent_history = s_values[-4:] 
             
             # Load Model (or use cached)
             model_path = "models/best_models/lstm_model.pth"
             lstm = PredictionService.load_lstm_model(model_path)
             
             if lstm:
                pred_value = PredictionService.predict_with_lstm(lstm, recent_history)
             else:
                pred_value = s_values[-1] # Fallback to naive persistence
                
             # Prediction anchor: always MAX(week_start_date) for this specific triple
             # Never use results[-1] — list ordering assumptions are fragile
             if true_last_date is None:
                 forecast = None
             else:
                 last_actual_date = true_last_date
                 next_week_start  = last_actual_date + timedelta(days=7)
                 next_week_end    = last_actual_date + timedelta(days=13)

                 # ── Phase 3B: Adaptive CI ──────────────────────────────────────
                 # Use rolling MAE from model_performance when ≥ 6 validated weeks exist.
                 # Fallback to static ±10% for cold-start or sparse targets.
                 _ci_fallback_half = 10.0
                 try:
                     perf_row = db.execute(text("""
                         SELECT mae_score, validated_count
                         FROM model_performance
                         WHERE ward        = :ward
                           AND organism    = :org
                           AND antibiotic  = :abx
                           AND model_name  = 'Phase3B_Rolling'
                         ORDER BY updated_at DESC
                         LIMIT 1
                     """), {"ward": ward, "org": organism, "abx": antibiotic}).fetchone()

                     if perf_row and perf_row[0] is not None and (perf_row[1] or 0) >= 6:
                         ci_half   = float(perf_row[0]) * 1.96
                         ci_source = "adaptive"
                     else:
                         ci_half   = _ci_fallback_half
                         ci_source = "static_fallback"
                 except Exception:
                     ci_half   = _ci_fallback_half
                     ci_source = "static_fallback"

                 ci_lower = max(0.0,   round(pred_value - ci_half, 1))
                 ci_upper = min(100.0, round(pred_value + ci_half, 1))

                 forecast = {
                     "week": f"Week of {next_week_start.strftime('%b %d, %Y')}",
                     "date": next_week_start.strftime("%b %d"),
                     "predicted_s": round(pred_value, 1),
                     "predicted_week_start": next_week_start.isoformat(),
                     "predicted_week_end":   next_week_end.isoformat(),
                     "ci_lower":             ci_lower,
                     "ci_upper":             ci_upper,
                     "ci_half_width":        round(ci_half, 2),
                     "ci_source":            ci_source,   # "adaptive" or "static_fallback"
                 }


             # ── Phase 4B + 4C: Adaptive tolerance + Drift + G8 hierarchy ─────
             baseline_val = baseline[-1]["expected_s"] if baseline else s_values[-1]
             observed_s   = s_values[-1]

             drift_analysis = {}
             try:
                 from models.drift_detector import run_drift_analysis

                 # ── Phase 4C (R6): Adaptive tolerance ─────────────────────────
                 # tolerance = min(max(rolling_mae × 2, rolling_std), 25.0)
                 # Computed before G8 alert classification
                 rolling_std = statistics.stdev(s_values) if len(s_values) >= 2 else 10.0

                 # Read Phase 3B rolling metrics for this target
                 perf_4c = db.execute(text("""
                     SELECT mae_score, mean_bias, degradation_flagged
                     FROM model_performance
                     WHERE ward = :ward AND organism = :org AND antibiotic = :abx
                       AND model_name = 'Phase3B_Rolling'
                     ORDER BY updated_at DESC LIMIT 1
                 """), {"ward": ward, "org": organism, "abx": antibiotic}).fetchone()

                 rolling_mae_4c  = float(perf_4c[0]) if perf_4c and perf_4c[0] else None
                 mean_bias_4c    = float(perf_4c[1]) if perf_4c and perf_4c[1] else None
                 degraded_4c     = bool(perf_4c[2])  if perf_4c and perf_4c[2] else False

                 if rolling_mae_4c is not None:
                     # R6: tolerance = min(max(rolling_mae × 2, rolling_std), 25.0)
                     adaptive_tolerance = min(max(rolling_mae_4c * 2, rolling_std), 25.0)
                 else:
                     adaptive_tolerance = max(rolling_std, 10.0)  # fallback

                 # ── Phase 4B: CUSUM + slope + volatility + G8 ─────────────────
                 # CHECK 6: Slice to last 16 weeks — prevents full multi-year history
                 #          from being passed to CPU-heavy CUSUM/OLS each request.
                 drift_history = s_values[-16:]

                 # CHECK 5: Read active model + validated_count for cold-start bypass
                 active_model_row = db.execute(text("""
                     SELECT model_name
                     FROM model_performance
                     WHERE ward = :ward AND organism = :org AND antibiotic = :abx
                       AND is_active = TRUE
                     LIMIT 1
                 """), {"ward": ward, "org": organism, "abx": antibiotic}).fetchone()
                 active_model_4b = active_model_row[0] if active_model_row else ""

                 validated_ct_row = db.execute(text("""
                     SELECT validated_count
                     FROM model_performance
                     WHERE ward = :ward AND organism = :org AND antibiotic = :abx
                     ORDER BY updated_at DESC LIMIT 1
                 """), {"ward": ward, "org": organism, "abx": antibiotic}).fetchone()
                 validated_count_4b = int(validated_ct_row[0]) if validated_ct_row and validated_ct_row[0] else 0

                 drift_analysis = run_drift_analysis(
                     history              = drift_history,
                     observed_s           = observed_s,
                     baseline_s           = baseline_val,
                     adaptive_tolerance   = adaptive_tolerance,
                     degradation_flagged  = degraded_4c,
                     mean_bias            = mean_bias_4c,
                     rolling_mae          = rolling_mae_4c,
                     validated_count      = validated_count_4b,   # CHECK 5
                     active_model         = active_model_4b,       # CHECK 5
                 )

                 # Primary G8 alert now drives the status field
                 # INSUFFICIENT_DATA falls back to GREEN for display
                 primary = drift_analysis.get("primary_alert", "GREEN")
                 status = primary if primary != "INSUFFICIENT_DATA" else "GREEN"


             except Exception as _drift_err:
                 logger.warning(f"Phase 4B drift analysis failed: {_drift_err}")
                 # Graceful fallback to Phase 3-era hybrid status
                 alert_status, _, _ = PredictionService.get_hybrid_status(
                     observed_s     = observed_s,
                     baseline_lower = baseline_val - 10,
                     lstm_forecast  = pred_value
                 )
                 status = alert_status.upper()
                 adaptive_tolerance = 10.0

             _, domain = PredictionService.generate_detailed_stewardship(
                 status.lower(), organism, antibiotic, ward
             )

        # ── Enrich drift_analysis with values the frontend needs for Panel B/D ──
        # These locals exist inside the `if len(s_values) >= 3` block.
        # Safe defaults cover cold-start / short-history targets.
        _obs   = observed_s   if len(s_values) >= 3 else (s_values[-1] if s_values else None)
        _base  = baseline_val if len(s_values) >= 3 else None
        _tol   = adaptive_tolerance if len(s_values) >= 3 else 10.0

        if isinstance(drift_analysis, dict):
            drift_analysis["observed_s"]         = round(_obs,  1) if _obs  is not None else None
            drift_analysis["baseline_s"]         = round(_base, 1) if _base is not None else None
            drift_analysis["adaptive_tolerance"] = round(_tol,  1)
            drift_analysis["degradation_flagged"]= degraded_4c     if len(s_values) >= 3 else False
            drift_analysis["mean_bias"]          = round(mean_bias_4c,   2) if (len(s_values) >= 3 and mean_bias_4c   is not None) else None
            drift_analysis["rolling_mae"]        = round(rolling_mae_4c, 2) if (len(s_values) >= 3 and rolling_mae_4c is not None) else None
            drift_analysis["validated_count"]    = validated_count_4b if len(s_values) >= 3 else 0
            drift_analysis["active_model_name"]  = active_model_4b   if len(s_values) >= 3 else "BASELINE_MEAN"

        return {
            "ward": ward,
            "organism": organism,
            "antibiotic": antibiotic,
            "history": history,
            "baseline": baseline,
            "forecast": forecast,
            "status": status,
            "stewardship_domain": domain,
            "drift_analysis": drift_analysis,   # G8 full alert structure — now enriched
            "engine_version": "Hybrid_LSTM_v4B",
            # model_performance: convenience top-level copy for Panel D
            "model_performance": {
                "active_model":         active_model_4b   if len(s_values) >= 3 else "BASELINE_MEAN",
                "rolling_mae":          round(rolling_mae_4c, 2) if (len(s_values) >= 3 and rolling_mae_4c is not None) else None,
                "mean_bias":            round(mean_bias_4c,   2) if (len(s_values) >= 3 and mean_bias_4c   is not None) else None,
                "degradation_flagged":  degraded_4c     if len(s_values) >= 3 else False,
                "validated_count":      validated_count_4b if len(s_values) >= 3 else 0,
                "ci_source":            forecast.get("ci_source")    if forecast else "static_fallback",
                "ci_half_width":        forecast.get("ci_half_width") if forecast else 10.0,
            },
        }

    except Exception as e:
        logger.error(f"Analysis Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

# Start of Dashboard Endpoints
@app.get("/api/dashboard/summary")
async def get_dashboard_summary():
    """
    Hospital Overview: List of wards with alert counts.
    Reflects the LATEST operational intelligence state.
    """
    db = SessionLocal()
    try:
        # Get latest log ID for each unique combo to avoid duplicates
        # Then aggregate by Ward
        query = """
            WITH LatestLogs AS (
                SELECT ward, alert_status, log_date,
                       ROW_NUMBER() OVER(PARTITION BY ward, organism, antibiotic ORDER BY log_date DESC) as rn
                FROM surveillance_logs
                -- SCOPE LOCK: Non-Fermenters only
                WHERE organism IN ('Pseudomonas aeruginosa', 'Acinetobacter baumannii')
            )
            SELECT 
                ward,
                COUNT(CASE WHEN alert_status = 'green' THEN 1 END) as green_count,
                COUNT(CASE WHEN alert_status = 'amber' OR alert_status = 'amber-high' THEN 1 END) as amber_count,
                COUNT(CASE WHEN alert_status = 'red' OR alert_status = 'critical' THEN 1 END) as red_count,
                MAX(log_date) as last_updated
            FROM LatestLogs
            WHERE rn = 1
            GROUP BY ward
            ORDER BY red_count DESC, amber_count DESC, ward ASC
        """
        results = db.execute(text(query)).fetchall()
        
        summary = []
        for row in results:
            summary.append({
                "ward": row[0],
                "active_alerts": row[2] + row[3], # Amber + Red
                "green": row[1],
                "amber": row[2],
                "red": row[3],
                "last_signal": row[4],
                "highest_severity": "Critical" if row[3] > 0 else "Warning" if row[2] > 0 else "Normal"
            })
            
        return {
            "hospital_summary": summary,
            "engine_version": "Hybrid_LSTM_v1",
            "run_mode": "SHADOW_VALIDATION",
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Dashboard Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/ward/{ward_id:path}/status")
async def get_ward_status(ward_id: str):
    """
    Ward Detail View: List of all bugs/drugs monitored in this ward.
    Uses 4-Week Weighted Average for smooth display of S%.
    """
    db = SessionLocal()
    try:
        # Fetch last 4 weeks for all targets in this ward
        query = """
            WITH RecentLogs AS (
                 SELECT organism, antibiotic, observed_s_percent, baseline_s_percent, predicted_s_percent,
                        alert_status, stewardship_domain, stewardship_prompt, log_date,
                        ROW_NUMBER() OVER(PARTITION BY organism, antibiotic ORDER BY log_date DESC) as rn
                 FROM surveillance_logs
                 -- SCOPE LOCK: Non-Fermenters only
                 WHERE ward = :ward
                   AND organism IN ('Pseudomonas aeruginosa', 'Acinetobacter baumannii')
            )
            SELECT organism, antibiotic, 
                   observed_s_percent, baseline_s_percent, predicted_s_percent,
                   alert_status, stewardship_domain, stewardship_prompt, log_date
            FROM RecentLogs
            WHERE rn <= 12
            ORDER BY organism, antibiotic, log_date DESC
        """
        results = db.execute(text(query), {"ward": ward_id}).fetchall()
        
        # Aggregate in Python
        details_map = {} # Key: (org, abx) -> { obs: [], base: [], pred: [], meta: {} }
        
        for row in results:
            org, abx = row[0], row[1]
            key = (org, abx)
            
            if key not in details_map:
                details_map[key] = {
                    "obs": [], "base": [], "pred": [],
                    # Capture metadata from the LATEST record (first one encountered due to sort)
                    "meta": {
                        "organism": org, "antibiotic": abx,
                        "status": row[5], "stewardship": row[6],
                        "prompt": row[7], "last_updated": row[8]
                    }
                }
            
            # Collect values for averaging
            d = details_map[key]
            if row[2] is not None: d["obs"].append(float(row[2]))
            if row[3] is not None: d["base"].append(float(row[3]))
            if row[4] is not None: d["pred"].append(float(row[4]))
            
        # Fetch last observed week per (organism, antibiotic) from aggregated data
        # This is the true last date with sufficient isolates — different from global last_data_week
        recency_query = """
            SELECT organism, antibiotic,
                   TO_CHAR(MAX(week_start_date), 'YYYY-MM-DD') as last_data_week
            FROM ast_weekly_aggregated
            WHERE ward = :ward
              AND organism IN ('Pseudomonas aeruginosa', 'Acinetobacter baumannii')
            GROUP BY organism, antibiotic
        """
        recency_rows = db.execute(text(recency_query), {"ward": ward_id}).fetchall()
        # Map (organism, antibiotic) -> last_data_week
        recency_map = { (r[0], r[1]): r[2] for r in recency_rows }

        # Build Final List
        details = []
        for (org, abx), d in details_map.items():
            obs_avg = sum(d["obs"]) / len(d["obs"]) if d["obs"] else 0.0
            base_avg = sum(d["base"]) / len(d["base"]) if d["base"] else 0.0
            pred_avg = sum(d["pred"]) / len(d["pred"]) if d["pred"] else 0.0
            
            # Calculate Trend based on SMOOTHED values
            trend = "→"
            if pred_avg < (obs_avg - 1.0): trend = "↓" 
            elif pred_avg > (obs_avg + 1.0): trend = "↑"
            
            details.append({
                **d["meta"],
                "current_s": round(obs_avg, 1),
                "baseline_s": round(base_avg, 1),
                "forecast_s": round(pred_avg, 1),
                "trend": trend,
                "last_data_week": recency_map.get((org, abx))  # None if no aggregated data
            })
            
        return {
            "ward_id": ward_id,
            "monitored_targets": sorted(details, key=lambda x: (x['status'] == 'red', x['status'] == 'amber'), reverse=True),
            "engine_version": "Hybrid_LSTM_v1"
        }
    except Exception as e:
        logger.error(f"Ward Detail Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/audit/logs")
async def get_audit_logs(limit: int = 50):
    """
    Audit Log Viewer for Traceability & Defense.
    """
    db = SessionLocal()
    try:
        query = """
            SELECT log_date, ward, organism, antibiotic, alert_status, 
                   forecast_deviation, model_version, alert_reason
            FROM surveillance_logs
            ORDER BY log_date DESC
            LIMIT :limit
        """
        results = db.execute(text(query), {"limit": limit}).fetchall()
        
        logs = []
        for row in results:
            logs.append({
                "timestamp": row[0],
                "ward": row[1],
                "organism": row[2],
                "antibiotic": row[3],
                "status": row[4],
                "deviation": float(row[5]) if row[5] else 0.0,
                "model_version": row[6],
                "reason": row[7]
            })
            
        return {
            "logs": logs,
            "engine_version": "Hybrid_LSTM_v1",
            "run_mode": "SHADOW"
        }
            
    except Exception as e:
        logger.error(f"Audit Log Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

# ============================================
# ESBL CDSS ENDPOINTS (Stage 9)
# ============================================
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from esbl_service import esbl_service, ValidationResponse

class ESBLEvaluateRequest(BaseModel):
    inputs: Dict[str, Any]
    ast_available: bool = False

class ESBLScopeRequest(BaseModel):
    organism: str
    gram: str

class ESBLOverrideRequest(BaseModel):
    encounter_id: str
    user_id: str
    model_version: str
    recommendation_id: str
    decision: str # OVERRIDE / ACCEPT
    reason_code: Optional[str] = None
    selected_antibiotic: Optional[str] = None

class ESBLPostASTRequest(BaseModel):
    empiric_drug: str
    ast_panel: Dict[str, str] # e.g. {"MEM": "S", "TZP": "R"}

@app.post("/api/esbl/evaluate")
async def evaluate_esbl_risk(request: ESBLEvaluateRequest):
    """
    Main CDSS Engine Endpoint.
    - Checks Governance (AST Lock, Scope).
    - Predicts Risk (Stage 5).
    - Generates Recommendations (Stage 7).
    - Flags OOD (Stage 9).
    """
    try:
        return esbl_service.predict_and_evaluate(request.dict())
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"ESBL Evaluate Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/esbl/validate-scope", response_model=ValidationResponse)
async def validate_esbl_scope(request: ESBLScopeRequest):
    """
    Pre-check to prevent out-of-scope usage in UI.
    """
    return esbl_service.validate_scope(request.organism, request.gram)

@app.post("/api/esbl/override")
async def log_esbl_override(request: ESBLOverrideRequest):
    """
    Audit logging for clinician overrides.
    Mandatory reason code if overriding.
    """
    # In a full system, this would write to the 'audit_logs' table defined in Stage 8.
    # For now, we log to file/console as a mock proof of governance.
    log_entry = request.dict()
    log_entry["timestamp"] = datetime.utcnow().isoformat()
    
    logger.info(f"🛡️ ESBL AUDIT LOG: {json.dumps(log_entry)}")
    
    # Save to a local JSONL file for verification
    with open("esbl_audit_log.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
        
    return {"status": "logged", "message": "Decision recorded in audit trail."}



# ============================================
# ESBL: Encounter Persistence (Backend - SQL)
# ============================================

@app.post("/api/encounters")
async def save_encounter(data: dict):
    """
    Save encounter to PostgreSQL with explicit columns.
    """
    db = SessionLocal()
    try:
        inputs = data.get("inputs", {})
        result = data.get("result", {})
        risk = result.get("risk", {})
        metadata = result.get("metadata", {})
        
        encounter_id = inputs.get("id")
        if not encounter_id:
            raise HTTPException(status_code=400, detail="Missing Encounter ID")

        # Insert with explicit columns
        query = text("""
            INSERT INTO esbl_encounters (
                encounter_id, age, gender, ward, organism, gram_stain,
                sample_type, cell_count_level, pus_type, pure_growth,
                esbl_probability, risk_group, ood_warning,
                model_version, evidence_version, threshold_version,
                recommendations, status, created_at
            ) VALUES (
                :enc_id, :age, :gender, :ward, :organism, :gram,
                :sample_type, :cell_count, :pus_type, :pure_growth,
                :esbl_prob, :risk_group, :ood_warning,
                :model_ver, :evidence_ver, :threshold_ver,
                :recommendations, :status, :created_at
            )
            ON CONFLICT (encounter_id) 
            DO UPDATE SET
                esbl_probability = :esbl_prob,
                risk_group = :risk_group,
                recommendations = :recommendations,
                updated_at = :created_at
        """)
        
        db.execute(query, {
            "enc_id": encounter_id,
            "age": int(inputs.get("Age", 0)) if inputs.get("Age") else None,
            "gender": inputs.get("Gender"),
            "ward": inputs.get("Ward"),
            "organism": inputs.get("Organism"),
            "gram": inputs.get("Gram"),
            "sample_type": inputs.get("Sample_Type"),
            "cell_count": inputs.get("Cell_Count_Level"),
            "pus_type": inputs.get("PUS_Type"),
            "pure_growth": inputs.get("Pure_Growth"),
            "esbl_prob": risk.get("probability"),
            "risk_group": risk.get("group"),
            "ood_warning": risk.get("ood_warning", False),
            "model_ver": metadata.get("model_version"),
            "evidence_ver": metadata.get("evidence_version"),
            "threshold_ver": metadata.get("threshold_version"),
            "recommendations": json.dumps(result.get("recommendations", [])),
            "status": "PENDING",
            "created_at": datetime.utcnow()
        })
        db.commit()
        
        # Also save to audit logs for governance tracking
        try:
            audit_query = text("""
                INSERT INTO esbl_audit_logs (
                    log_date, encounter_id, ward, organism, age,
                    esbl_probability, risk_group, top_recommendation,
                    recommendation_efficacy, model_version, ood_detected
                ) VALUES (
                    :log_date, :enc_id, :ward, :organism, :age,
                    :esbl_prob, :risk_group, :top_rec,
                    :top_efficacy, :model_ver, :ood_detected
                )
            """)
            
            # Extract top recommendation
            recommendations = result.get("recommendations", [])
            top_drug = recommendations[0].get("drug", "N/A") if recommendations else "N/A"
            top_efficacy = recommendations[0].get("success_prob", 0) if recommendations else 0
            
            db.execute(audit_query, {
                "log_date": datetime.utcnow(),
                "enc_id": encounter_id,
                "ward": inputs.get("Ward"),
                "organism": inputs.get("Organism"),
                "age": int(inputs.get("Age", 0)) if inputs.get("Age") else None,
                "esbl_prob": risk.get("probability"),
                "risk_group": risk.get("group"),
                "top_rec": top_drug,
                "top_efficacy": top_efficacy,
                "model_ver": metadata.get("model_version"),
                "ood_detected": risk.get("ood_warning", False)
            })
            db.commit()
        except Exception as audit_err:
            logger.warning(f"Failed to save audit log: {audit_err}")
            # Don't fail the main save if audit fails
            
        return {"status": "success", "message": f"Encounter {encounter_id} saved to Database."}
            
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save encounter to DB: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/encounters/{encounter_id}")
async def get_encounter(encounter_id: str):
    """
    Retrieve encounter from SQL Database.
    """
    db = SessionLocal()
    try:
        query = text("""
            SELECT 
                encounter_id, age, gender, ward, organism, gram_stain,
                sample_type, cell_count_level, pus_type, pure_growth,
                esbl_probability, risk_group, ood_warning,
                model_version, evidence_version, threshold_version,
                recommendations, status
            FROM esbl_encounters 
            WHERE encounter_id = :id
        """)
        row = db.execute(query, {"id": encounter_id}).fetchone()
        
        if row:
            # Reconstruct the format expected by frontend
            return {
                "inputs": {
                    "id": row[0],
                    "Age": str(row[1]) if row[1] else "",
                    "Gender": row[2] or "",
                    "Ward": row[3] or "",
                    "Organism": row[4] or "",
                    "Gram": row[5] or "",
                    "Sample_Type": row[6] or "",
                    "Cell_Count_Level": row[7] or "",
                    "PUS_Type": row[8] or "",
                    "Pure_Growth": row[9] or ""
                },
                "result": {
                    "risk": {
                        "probability": float(row[10]) if row[10] else 0,
                        "group": row[11] or "Low",
                        "ood_warning": row[12] or False
                    },
                    "metadata": {
                        "model_version": row[13] or "",
                        "evidence_version": row[14] or "",
                        "threshold_version": row[15] or ""
                    },
                    "recommendations": row[16] if row[16] else []
                }
            }
        else:
            raise HTTPException(status_code=404, detail="Encounter ID not found in Database.")
            
    except Exception as e:
        logger.error(f"Failed to fetch encounter from DB: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/esbl/lab-results/{encounter_id}")
async def get_lab_results(encounter_id: str):
    """
    Fetch confirmed lab results for an encounter.
    """
    db = SessionLocal()
    try:
        query = text("""
            SELECT antibiotic, result
            FROM esbl_lab_results
            WHERE encounter_id = :enc_id
            ORDER BY antibiotic
        """)
        
        rows = db.execute(query, {"enc_id": encounter_id}).fetchall()
        
        if not rows:
            raise HTTPException(status_code=404, detail="No lab results found for this encounter.")
        
        # Convert to dict
        results = {row[0]: row[1] for row in rows}
        return {"encounter_id": encounter_id, "results": results}
        
    except Exception as e:
        logger.error(f"Failed to fetch lab results: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/esbl/audit-logs")
async def get_esbl_audit_logs():
    """
    Fetch ESBL governance/audit logs for the dashboard.
    """
    db = SessionLocal()
    try:
        query = text("""
            SELECT 
                id, log_date, encounter_id, ward, organism, age,
                esbl_probability, risk_group, top_recommendation,
                recommendation_efficacy, model_version, ood_detected
            FROM esbl_audit_logs
            ORDER BY log_date DESC
            LIMIT 100
        """)
        
        rows = db.execute(query).fetchall()
        
        logs = []
        for row in rows:
            logs.append({
                "id": row[0],
                "timestamp": row[1].isoformat() if row[1] else None,
                "encounter_id": row[2],
                "ward": row[3],
                "organism": row[4],
                "age": row[5],
                "esbl_probability": float(row[6]) if row[6] else 0,
                "risk_group": row[7],
                "top_recommendation": row[8],
                "recommendation_efficacy": float(row[9]) if row[9] else 0,
                "model_version": row[10],
                "ood_detected": row[11]
            })
        
        return {"logs": logs, "total": len(logs)}
        
    except Exception as e:
        logger.error(f"Failed to fetch audit logs: {e}")
        # Return empty if table doesn't have data yet
        return {"logs": [], "total": 0}
    finally:
        db.close()

@app.post("/api/esbl/post-ast-review")
async def post_ast_review(request: ESBLPostASTRequest):
    """
    Stage 8: Confirmatory Stewardship & De-escalation Rules.
    """
    # Simplified Logic from post_ast_rules.json
    empiric = request.empiric_drug
    panel = request.ast_panel
    
    feedback = {
        "action": "MAINTAIN",
        "message": "Continue current therapy.",
        "alert_level": "GREEN"
    }
    
    # Rule 1: Resistance Check
    if panel.get(empiric) == "R":
        feedback = {
            "action": "ESCALATION_REQUIRED",
            "message": f"Pathogen is RESISTANT to Empiric Choice ({empiric}). Change therapy immediately.",
            "alert_level": "RED"
        }
    
    # Rule 2: De-escalation (Carbapenem Sparing)
    elif empiric in ["MEM", "IMP", "ETP"] and panel.get("TZP") == "S":
         feedback = {
            "action": "DE_ESCALATION_RECOMMENDED",
            "message": "Pathogen is sensitive to Pip-Tazo. De-escalate from Carbapenem.",
            "alert_level": "YELLOW"
        }
        
    # Rule 3: ESBL Negative check?
    # (Requires knowing if ESBL-neg, inferred from CTX/CRO S status often).
    elif panel.get("CTX") == "S" and panel.get("CRO") == "S":
         if empiric in ["MEM", "IMP", "ETP"]:
             feedback = {
                "action": "DE_ESCALATION_RECOMMENDED",
                "message": "Non-ESBL phenotype detected. Carbapenem not required.",
                "alert_level": "YELLOW"
            }

    return feedback



@app.get("/api/mrsa/validation-logs")
async def get_mrsa_validation_logs():
    """
    Fetch Stage D Validation Status.
    """
    db = SessionLocal()
    try:
        query = text("""
            SELECT id, validation_date, ward, sample_type, 
                   consensus_band, cefoxitin_result, actual_mrsa, consensus_correct
            FROM mrsa_validation_log
            ORDER BY validation_date DESC
            LIMIT 50
        """)
        results = db.execute(query).fetchall()
        
        logs = []
        for row in results:
            logs.append({
                "id": row[0],
                "validation_date": row[1].isoformat(),
                "ward": row[2],
                "sample_type": row[3],
                "consensus_band": row[4],
                "cefoxitin_result": row[5],
                "actual_mrsa": row[6],
                "consensus_correct": row[7]
            })
        return logs
    except Exception as e:
        logger.error(f"Validation Log Fetch Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/analysis/antibiogram")
async def get_antibiogram(ward: Optional[str] = None):
    """
    Generate Accumulative Antibiogram Matrix (Organism vs Antibiotic).

    ARCHITECTURE NOTE:
    Reads from `ast_weekly_aggregated` — the true epidemiological data layer.
    NOT from `surveillance_logs` (which is the AI prediction audit table).

    Antibiogram = what is the current S% in the dataset?
    That answer must come from aggregated AST data, not from prediction logs.

    This ensures ALL organisms appear regardless of whether the AI engine
    has been triggered for them — preventing silent data invisibility.
    """
    db = SessionLocal()
    try:
        # ----------------------------------------------------------------
        # LAYER 1: DATA LAYER — ast_weekly_aggregated
        # Get the most recent week's S% per (ward, organism, antibiotic)
        # as the current observed value.
        # ----------------------------------------------------------------
        if ward:
            current_query = text("""
                WITH RankedWeeks AS (
                    SELECT
                        ward,
                        organism,
                        antibiotic,
                        susceptibility_percent,
                        week_start_date,
                        ROW_NUMBER() OVER (
                            PARTITION BY ward, organism, antibiotic
                            ORDER BY week_start_date DESC
                        ) AS rn
                    FROM ast_weekly_aggregated
                    WHERE ward = :ward
                      AND total_tested >= 3
                      AND susceptibility_percent IS NOT NULL
                )
                SELECT organism, antibiotic, susceptibility_percent
                FROM RankedWeeks
                WHERE rn = 1
            """)
            params = {"ward": ward}
        else:
            # Hospital-wide: aggregate all wards together for the latest week
            current_query = text("""
                WITH OrgWeekly AS (
                    SELECT
                        organism,
                        antibiotic,
                        week_start_date,
                        SUM(susceptible_count)  AS total_s,
                        SUM(total_tested)       AS total_n
                    FROM ast_weekly_aggregated
                    WHERE total_tested >= 3
                    GROUP BY organism, antibiotic, week_start_date
                ),
                RankedWeeks AS (
                    SELECT
                        organism,
                        antibiotic,
                        week_start_date,
                        CASE WHEN total_n > 0
                            THEN ROUND((total_s::NUMERIC / total_n::NUMERIC) * 100, 2)
                            ELSE NULL
                        END AS susceptibility_percent,
                        ROW_NUMBER() OVER (
                            PARTITION BY organism, antibiotic
                            ORDER BY week_start_date DESC
                        ) AS rn
                    FROM OrgWeekly
                    WHERE total_n > 0
                )
                SELECT organism, antibiotic, susceptibility_percent
                FROM RankedWeeks
                WHERE rn = 1
                  AND susceptibility_percent IS NOT NULL
            """)
            params = {}

        current_rows = db.execute(current_query, params).fetchall()

        # ----------------------------------------------------------------
        # LAYER 2: HISTORY — last 4 weeks for sparkline trend display
        # ----------------------------------------------------------------
        if ward:
            history_query = text("""
                WITH RankedWeeks AS (
                    SELECT
                        organism,
                        antibiotic,
                        susceptibility_percent,
                        week_start_date,
                        ROW_NUMBER() OVER (
                            PARTITION BY organism, antibiotic
                            ORDER BY week_start_date DESC
                        ) AS rn
                    FROM ast_weekly_aggregated
                    WHERE ward = :ward
                      AND total_tested >= 3
                      AND susceptibility_percent IS NOT NULL
                )
                SELECT organism, antibiotic, susceptibility_percent
                FROM RankedWeeks
                WHERE rn <= 4
                ORDER BY organism, antibiotic, week_start_date ASC
            """)
            history_params = {"ward": ward}
        else:
            history_query = text("""
                WITH OrgWeekly AS (
                    SELECT
                        organism,
                        antibiotic,
                        week_start_date,
                        SUM(susceptible_count) AS total_s,
                        SUM(total_tested)      AS total_n
                    FROM ast_weekly_aggregated
                    WHERE total_tested >= 3
                    GROUP BY organism, antibiotic, week_start_date
                ),
                Computed AS (
                    SELECT
                        organism,
                        antibiotic,
                        week_start_date,
                        ROUND((total_s::NUMERIC / total_n::NUMERIC) * 100, 2) AS susceptibility_percent,
                        ROW_NUMBER() OVER (
                            PARTITION BY organism, antibiotic
                            ORDER BY week_start_date DESC
                        ) AS rn
                    FROM OrgWeekly
                    WHERE total_n > 0
                )
                SELECT organism, antibiotic, susceptibility_percent
                FROM Computed
                WHERE rn <= 4
                ORDER BY organism, antibiotic, week_start_date ASC
            """)
            history_params = {}

        history_rows = db.execute(history_query, history_params).fetchall()

        # ----------------------------------------------------------------
        # LAYER 3 (Optional): Pull latest AI forecast from surveillance_logs
        # for the "Predicted" toggle — this is the ONLY place surveillance_logs
        # is used, and only as a supplemental AI layer, not as the primary source.
        # ----------------------------------------------------------------
        if ward:
            pred_query = text("""
                WITH LatestPred AS (
                    SELECT organism, antibiotic, predicted_s_percent,
                           ROW_NUMBER() OVER (
                               PARTITION BY organism, antibiotic
                               ORDER BY log_date DESC
                           ) AS rn
                    FROM surveillance_logs
                    WHERE ward = :ward
                      AND predicted_s_percent IS NOT NULL
                )
                SELECT organism, antibiotic, predicted_s_percent
                FROM LatestPred WHERE rn = 1
            """)
            pred_params = {"ward": ward}
        else:
            pred_query = text("""
                WITH LatestPred AS (
                    SELECT organism, antibiotic, predicted_s_percent,
                           ROW_NUMBER() OVER (
                               PARTITION BY organism, antibiotic
                               ORDER BY log_date DESC
                           ) AS rn
                    FROM surveillance_logs
                    WHERE predicted_s_percent IS NOT NULL
                      AND ward IS NULL
                )
                SELECT organism, antibiotic, predicted_s_percent
                FROM LatestPred WHERE rn = 1
            """)
            pred_params = {}

        pred_rows = db.execute(pred_query, pred_params).fetchall()

        # ----------------------------------------------------------------
        # BUILD MATRIX
        # ----------------------------------------------------------------
        antibiotics_set = set()
        matrix = {}

        # Index history
        history_index = {}  # (org, abx) -> [s%, s%, ...]
        for row in history_rows:
            org, abx, val = row
            key = (org, abx)
            if key not in history_index:
                history_index[key] = []
            if val is not None:
                history_index[key].append(float(val))

        # Index predicted values (from AI layer)
        pred_index = {}  # (org, abx) -> predicted_s%
        for row in pred_rows:
            org, abx, val = row
            if val is not None:
                pred_index[(org, abx)] = round(float(val), 1)

        def compute_ewma_forecast(history: list, alpha: float = 0.4) -> float:
            """
            Exponential-weighted moving average (EWMA) forecast.
            Applies heavier weight to recent weeks — same logic as SMAModel in
            models/sma_model.py (alpha=0.3 there, slightly higher here for responsiveness).
            Returns the next-step forecast as a float clamped to [0, 100].
            """
            if not history:
                return None
            if len(history) == 1:
                return round(history[0], 1)
            # Build weights: most-recent week gets highest weight
            n = len(history)
            weights = [(1 - alpha) ** i for i in range(n)]
            weights.reverse()  # oldest → newest
            total_w = sum(weights)
            ewma = sum(w * v for w, v in zip(weights, history)) / total_w
            return round(float(max(0.0, min(100.0, ewma))), 1)

        # Build matrix from current S% (data layer is authoritative)
        for row in current_rows:
            org, abx, curr_val = row
            if curr_val is None:
                continue

            antibiotics_set.add(abx)
            if org not in matrix:
                matrix[org] = {}

            key = (org, abx)
            history = history_index.get(key, [])

            # --- Predicted value resolution (3-tier priority) ---
            # Priority 1: Real LSTM forecast from surveillance_logs
            #             (only exists for organisms the cron sweep has run)
            if key in pred_index:
                predicted = pred_index[key]
                forecast_method = "LSTM"
                has_forecast = True

            # Priority 2: Statistical EWMA computed from aggregated weekly history
            #             (covers ALL organisms regardless of surveillance sweep coverage,
            #              e.g. Staphylococcus aureus which is handled by the MRSA module)
            elif history:
                predicted = compute_ewma_forecast(history)
                forecast_method = "EWMA-Stat"
                has_forecast = True

            # Priority 3: Genuinely no data at all — cannot forecast
            else:
                predicted = None
                forecast_method = None
                has_forecast = False

            matrix[org][abx] = {
                "current": round(float(curr_val), 1),
                "predicted": predicted,
                "has_forecast": has_forecast,
                "forecast_method": forecast_method,
                "history": history
            }

        # ----------------------------------------------------------------
        # LAYER 4: Last data week — for correct date labelling in UI
        # The UI must show the date of the last actual data point, 
        # NOT the current system clock date. This is the epidemiological
        # time reference for both "Current Observed" and "Predicted" views.
        # ----------------------------------------------------------------
        last_week_row = db.execute(text("""
            SELECT MAX(week_start_date) FROM ast_weekly_aggregated
            WHERE organism IN ('Pseudomonas aeruginosa', 'Acinetobacter baumannii')
              AND total_tested >= 3
        """)).fetchone()
        last_data_week = last_week_row[0] if last_week_row and last_week_row[0] else None
        predicted_week_start = None
        if last_data_week:
            from datetime import timedelta
            predicted_week_start = (last_data_week + timedelta(days=7)).isoformat()
            last_data_week = last_data_week.isoformat()

        return {
            "matrix": matrix,
            "antibiotics": sorted(list(antibiotics_set)),
            "scope": f"Ward {ward}" if ward else "Hospital-Wide",
            "last_data_week": last_data_week,
            "predicted_week_start": predicted_week_start,
        }

    except Exception as e:
        logger.error(f"Antibiogram Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

# --- Stage E: Analytics & Governance Endpoints ---
from mrsa_analytics_service import mrsa_analytics_service
from mrsa_schemas import GovernanceDecisionCreate

@app.get("/api/mrsa/analytics/summary")
async def get_analytics_summary():
    db = SessionLocal()
    try:
        return mrsa_analytics_service.get_summary(db)
    finally:
        db.close()

@app.get("/api/mrsa/analytics/heatmap")
async def get_ward_risk_heatmap():
    db = SessionLocal()
    try:
        return mrsa_analytics_service.get_ward_risk_heatmap(db)
    finally:
        db.close()

@app.post("/api/mrsa/governance/decision")
async def log_governance_decision(decision: GovernanceDecisionCreate):
    # Todo: Add User Auth Context (RBAC) here.
    # For now, using mock 'Admin' user.
    admin_user = "admin_user" 
    db = SessionLocal()
    try:
        mrsa_analytics_service.log_decision(db, decision, admin_user)
        return {"status": "Logged"}
    finally:
        db.close()

@app.post("/api/mrsa/predict", response_model=MRSAPredictionResponse, tags=["MRSA"])
async def predict_mrsa_risk(
    request: MRSAPredictionRequest, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Generate MRSA Risk Assessment (Pre-AST).
    Strictly restricted to Staphylococcus aureus inputs.
    """
    return mrsa_service.predict(db, request)

@app.get("/api/mrsa/explain/{assessment_id}", response_model=MRSAExplanationResponse, tags=["MRSA"])
async def explain_mrsa_risk(
    assessment_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Explain a specific risk assessment using stored snapshot.
    """
    return mrsa_service.explain(db, assessment_id)

# ============================================
# Master Data Routes
# ============================================
@app.get("/api/master/definitions/{category}", response_model=List[MasterDefinitionResponse], tags=["Configuration"])
def get_master_definitions(category: str, db: Session = Depends(get_db)):
    """Fetch active options for a category (WARD, SAMPLE_TYPE)"""
    return MasterDataService.get_definitions_by_category(db, category)

@app.post("/api/master/definitions", response_model=MasterDefinitionResponse, tags=["Configuration"])
def create_master_definition(def_in: MasterDefinitionCreate, db: Session = Depends(get_db)):
    """Add a new option to master data"""
    return MasterDataService.create_definition(db, def_in)

@app.delete("/api/master/definitions/{id}", tags=["Configuration"])
def delete_master_definition(id: int, db: Session = Depends(get_db)):
    """Soft delete a master data definition"""
    return MasterDataService.delete_definition(db, id)

# ============================================
# PANEL CONFIGURATION ROUTES (Phase 2.5)
# ============================================
import re as _re
from utils.normalization import normalize_antibiotic, normalize_organism

# ── In-memory panel cache ────────────────────────────────────────────────────
# Keyed by normalize_organism(name) → set of normalize_antibiotic(abx_name)
# Populated at startup and refreshed after any panel write.
_panel_cache: dict = {}

def refresh_panel_cache(db: Session):
    """Reload panel config from DB into _panel_cache. Called at startup + after writes."""
    global _panel_cache
    try:
        rows = db.execute(text("""
            SELECT o.name, a.name
            FROM organism_antibiotic_panel oap
            JOIN organisms  o ON oap.organism_id  = o.id
            JOIN antibiotics a ON oap.antibiotic_id = a.id
            WHERE o.is_active = TRUE AND a.is_active = TRUE AND oap.is_active = TRUE
        """)).fetchall()
        cache: dict = {}
        for org_name, abx_name in rows:
            cache.setdefault(normalize_organism(org_name), set()).add(
                normalize_antibiotic(abx_name)
            )
        _panel_cache = cache
        logger.info(f"Panel cache refreshed: {len(cache)} organisms loaded.")
    except Exception as e:
        logger.warning(f"Panel cache refresh failed (non-fatal): {e}")

@app.on_event("startup")
async def load_panel_cache_on_startup():
    """Warm the panel cache so aggregation can use it immediately."""
    db = next(get_db())
    try:
        refresh_panel_cache(db)
    finally:
        db.close()

def get_panel_cache() -> dict:
    """Return the current in-memory panel cache."""
    return _panel_cache

# ── READ endpoints ────────────────────────────────────────────────────────────

@app.get("/api/panels/organisms", tags=["Panel Configuration"])
def list_organisms(db: Session = Depends(get_db)):
    """List all active organisms."""
    rows = db.execute(text(
        "SELECT id, name, group_name FROM organisms WHERE is_active = TRUE ORDER BY group_name, name"
    )).fetchall()
    return [{"id": r[0], "name": r[1], "group_name": r[2]} for r in rows]


@app.get("/api/panels/antibiotics", tags=["Panel Configuration"])
def list_antibiotics(db: Session = Depends(get_db)):
    """List all active antibiotics (master list)."""
    rows = db.execute(text(
        "SELECT id, name, short_code FROM antibiotics WHERE is_active = TRUE ORDER BY name"
    )).fetchall()
    return [
        {
            "id": r[0], "name": r[1], "short_code": r[2],
            "display_name": f"{r[1]} ({r[2]})" if r[2] else r[1]
        }
        for r in rows
    ]


@app.get("/api/panels/cache-status", tags=["Panel Configuration"])
def panel_cache_status():
    """Debug: return count of organisms and antibiotics currently in memory cache."""
    total_abx = sum(len(v) for v in _panel_cache.values())
    return {"organisms_in_cache": len(_panel_cache), "antibiotics_in_cache": total_abx}


@app.get("/api/panels/{organism}", tags=["Panel Configuration"])
def get_organism_panel(organism: str, db: Session = Depends(get_db)):
    """Return the antibiotic panel for a given organism, with display_name."""
    rows = db.execute(text("""
        SELECT a.id, a.name, a.short_code
        FROM organism_antibiotic_panel oap
        JOIN organisms  o ON oap.organism_id  = o.id
        JOIN antibiotics a ON oap.antibiotic_id = a.id
        WHERE LOWER(o.name) = LOWER(:org)
          AND o.is_active = TRUE AND a.is_active = TRUE AND oap.is_active = TRUE
        ORDER BY a.name
    """), {"org": organism}).fetchall()
    return [
        {
            "id": r[0], "name": r[1], "short_code": r[2],
            "display_name": f"{r[1]} ({r[2]})" if r[2] else r[1]
        }
        for r in rows
    ]

# ── WRITE endpoints (admin only in future — guarded by current_user dep) ─────

@app.post("/api/panels/organisms", tags=["Panel Configuration"])
def create_organism(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new organism (admin only). Case-insensitive duplicate prevention."""
    name = payload.get("name", "").strip().title()
    group = payload.get("group_name", "General").strip()
    if not name:
        raise HTTPException(400, "name is required")
    existing = db.execute(
        text("SELECT 1 FROM organisms WHERE LOWER(name) = LOWER(:n)"), {"n": name}
    ).fetchone()
    if existing:
        raise HTTPException(400, f"Organism '{name}' already exists.")
    db.execute(
        text("INSERT INTO organisms (name, group_name) VALUES (:n, :g)"),
        {"n": name, "g": group}
    )
    db.commit()
    refresh_panel_cache(db)
    return {"status": "created", "name": name}


@app.post("/api/panels/antibiotics", tags=["Panel Configuration"])
def create_antibiotic(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new antibiotic (admin only). Case-insensitive duplicate prevention."""
    name = payload.get("name", "").strip().title()
    short_code = payload.get("short_code", "").strip().upper() or None
    if not name:
        raise HTTPException(400, "name is required")
    existing = db.execute(
        text("SELECT 1 FROM antibiotics WHERE LOWER(name) = LOWER(:n)"), {"n": name}
    ).fetchone()
    if existing:
        raise HTTPException(400, f"Antibiotic '{name}' already exists.")
    db.execute(
        text("INSERT INTO antibiotics (name, short_code) VALUES (:n, :s)"),
        {"n": name, "s": short_code}
    )
    db.commit()
    refresh_panel_cache(db)
    return {"status": "created", "name": name, "short_code": short_code}


@app.post("/api/panels/mapping", tags=["Panel Configuration"])
def add_panel_mapping(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign an antibiotic to an organism panel (admin only)."""
    org_id = payload.get("organism_id")
    abx_id = payload.get("antibiotic_id")
    if not org_id or not abx_id:
        raise HTTPException(400, "organism_id and antibiotic_id are required")
    # Upsert: if soft-deleted mapping exists, re-activate it
    db.execute(text("""
        INSERT INTO organism_antibiotic_panel (organism_id, antibiotic_id, is_active)
        VALUES (:org, :abx, TRUE)
        ON CONFLICT (organism_id, antibiotic_id) DO UPDATE SET is_active = TRUE
    """), {"org": org_id, "abx": abx_id})
    db.commit()
    refresh_panel_cache(db)
    return {"status": "mapped", "organism_id": org_id, "antibiotic_id": abx_id}


@app.delete("/api/panels/mapping/{org_id}/{abx_id}", tags=["Panel Configuration"])
def remove_panel_mapping(
    org_id: int,
    abx_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soft-delete: remove antibiotic from organism panel (admin only). Historical data untouched."""
    result = db.execute(text("""
        UPDATE organism_antibiotic_panel
        SET is_active = FALSE
        WHERE organism_id = :org AND antibiotic_id = :abx
    """), {"org": org_id, "abx": abx_id})
    db.commit()
    refresh_panel_cache(db)
    if result.rowcount == 0:
        raise HTTPException(404, "Mapping not found")
    return {"status": "removed", "organism_id": org_id, "antibiotic_id": abx_id}

# ============================================
# STP STAGE 1: SURVEILLANCE ENDPOINTS
# ============================================
# M9: CLINICAL NON-DECISION DISCLAIMER
# The STP surveillance system is for retrospective research only.
# NOT for patient-specific clinical decision support.
# ============================================

from data_processor.stp_stage_1_ingest import ingest_stp_data
from data_processor.stp_wide_to_long_transform import transform_wide_to_long
from data_processor.stp_build_antibiotic_registry import build_antibiotic_registry
from data_processor.stp_generate_governance_report import generate_governance_report
from data_processor.stp_descriptive_stats import compute_descriptive_stats
from data_processor.stp_populate_column_provenance import populate_column_provenance
from pydantic import BaseModel

class STPIngestRequest(BaseModel):
    dataset_version: str = "v1.0.0"
    force_reload: bool = False
    dry_run: bool = False

class STPFreezeRequest(BaseModel):
    dataset_version: str
    approved_by: str

@app.post("/api/stp/stage1/ingest", tags=["STP Surveillance"])
async def stp_ingest_pipeline(
    request: STPIngestRequest,
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    """
    STP Stage 1: Trigger complete ingestion pipeline.
    
    Process:
    1. Ingest & validate Excel data (M6 freeze check)
    2. Transform wide→long
    3. Build antibiotic registry
    4. Generate governance report (M1-M10, O1-O2)
    5. Compute descriptive stats (M3)
    6. Populate column provenance (M7)
    
    Security: Requires authentication
    M9: Research use only, NOT for clinical decisions
    """
    try:
        logger.info(f"🚀 STP Stage 1 Ingestion Started by {current_user.username}")
        logger.info(f"   Version: {request.dataset_version}")
        logger.info(f"   Force Reload: {request.force_reload}")
        
        # Step 1: Ingest (with M6 freeze enforcement)
        logger.info("Step 1/6: Ingesting & validating data...")
        ingest_result = ingest_stp_data(
            dataset_version=request.dataset_version,
            force_reload=request.force_reload
        )
        
        if ingest_result.get('status') == 'skipped':
            return {
                "status": "skipped",
                "message": f"Dataset {request.dataset_version} already exists. Use force_reload=True to overwrite.",
                "details": ingest_result
            }
        
        # Step 2: Transform
        logger.info("Step 2/6: Transforming wide→long...")
        transform_result = transform_wide_to_long(dataset_version=request.dataset_version)
        
        # Step 3: Antibiotic registry
        logger.info("Step 3/6: Building antibiotic registry...")
        registry_result = build_antibiotic_registry(dataset_version=request.dataset_version)
        
        # Step 4: Governance report (M1-M10, O1-O2)
        logger.info("Step 4/6: Generating governance report...")
        governance_result = generate_governance_report(dataset_version=request.dataset_version)
        
        # Step 5: Descriptive stats (M3)
        logger.info("Step 5/6: Computing descriptive statistics...")
        stats_result = compute_descriptive_stats(dataset_version=request.dataset_version)
        
        # Step 6: Column provenance (M7)
        logger.info("Step 6/6: Populating column provenance...")
        provenance_result = populate_column_provenance(dataset_version=request.dataset_version)
        
        logger.info("✅ STP Stage 1 Ingestion Complete!")
        
        return {
            "status": "success",
            "message": "STP Stage 1 pipeline completed successfully",
            "dataset_version": request.dataset_version,
            "results": {
                "ingestion": ingest_result,
                "transformation": transform_result,
                "antibiotic_registry": registry_result,
                "governance": governance_result,
                "statistics": {"status": "success"},
                "column_provenance": provenance_result
            },
            "clinical_disclaimer": "M9: This system is for research only, NOT for clinical decision support"
        }
    
    except ValueError as e:
        # M6 freeze violation or other validation error
        logger.error(f"❌ STP Ingestion failed: {e}")
        raise HTTPException(status_code=403, detail=str(e))
    
    except Exception as e:
        logger.error(f"❌ STP Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stp/stage1/metadata", tags=["STP Surveillance"])
async def get_stp_metadata(
    dataset_version: str = "v1.0.0",
    db: Session = Depends(get_db)
):
    """
    Get STP dataset metadata & provenance.
    
    Returns:
    - Dataset version & hash
    - Data quality metrics
    - Temporal coverage
    - Antibiotic registry
    - M5 schema version
    
    Security: Public (metadata only)
    """
    try:
        # Fetch metadata
        metadata_query = text("""
            SELECT 
                dataset_version, source_file_name, source_file_hash,
                total_rows_processed, total_rows_accepted, total_rows_rejected,
                date_range_start, date_range_end,
                schema_version, schema_checksum, is_frozen, approved_at
            FROM stp_dataset_metadata
            WHERE dataset_version = :v
        """)
        
        metadata = db.execute(metadata_query, {"v": dataset_version}).fetchone()
        
        if not metadata:
            raise HTTPException(status_code=404, detail=f"Dataset version {dataset_version} not found")
        
        # Fetch organism counts
        organism_query = text("""
            SELECT organism, COUNT(DISTINCT isolate_id) as count
            FROM stp_canonical_long
            WHERE dataset_version = :v
            GROUP BY organism
            ORDER BY count DESC
        """)
        organisms = {row[0]: row[1] for row in db.execute(organism_query, {"v": dataset_version}).fetchall()}
        
        # Fetch ward counts
        ward_query = text("""
            SELECT ward, COUNT(DISTINCT isolate_id) as count
            FROM stp_canonical_long
            WHERE dataset_version = :v
            GROUP BY ward
            ORDER BY count DESC
        """)
        wards = {row[0]: row[1] for row in db.execute(ward_query, {"v": dataset_version}).fetchall()}
        
        # Fetch antibiotic registry
        ab_query = text("""SELECT antibiotic_name, coverage_percent FROM stp_antibiotic_registry WHERE dataset_version = :v ORDER BY coverage_percent DESC""")
        antibiotics = [{"name": row[0], "coverage": float(row[1])} for row in db.execute(ab_query, {"v": dataset_version}).fetchall()]
        
        return {
            "dataset_version": metadata[0],
            "source_file": metadata[1],
            "source_hash": metadata[2],
            "rows_processed": metadata[3],
            "rows_accepted": metadata[4],
            "rows_rejected": metadata[5],
            "date_range": {
                "start": str(metadata[6]) if metadata[6] else None,
                "end": str(metadata[7]) if metadata[7] else None
            },
            "schema_version": metadata[8],  # M5
            "schema_checksum": metadata[9],  # M5
            "is_frozen": metadata[10],  # M6
            "approved_at": str(metadata[11]) if metadata[11] else None,  # M6
            "organism_counts": organisms,
            "ward_counts": wards,
            "antibiotic_registry": antibiotics
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Metadata fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stp/stage1/governance", tags=["STP Surveillance"])
async def get_stp_governance(
    dataset_version: str = "v1.0.0",
    db: Session = Depends(get_db)
):
    """
    Get STP governance documentation (M1-M10, O1-O2).
    
    Security: Public (for transparency)
    """
    try:
        query = text("""
            SELECT declaration_type, declaration_text
            FROM stp_governance_declarations
            WHERE dataset_version = :v
            AND is_active = TRUE
        """)
        
        declarations = db.execute(query, {"v": dataset_version}).fetchall()
        
        if not declarations:
            raise HTTPException(status_code=404, detail=f"No governance declarations found for {dataset_version}")
        
        return {
            "dataset_version": dataset_version,
            "declarations": {row[0]: row[1] for row in declarations},
            "compliance": "M1-M10 + O1-O2 complete"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Governance fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stp/stage1/quality-log", tags=["STP Surveillance"])
async def get_stp_quality_log(
    dataset_version: str = "v1.0.0",
    limit: int = 100,
    rejection_reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get STP data quality audit trail.
    
    Security: Requires authentication
    """
    try:
        query = """
            SELECT row_index, rejection_reason, organism_provided, 
                   ward_provided, sample_date_provided, details, created_at
            FROM stp_data_quality_log
            WHERE dataset_version = :v
        """
        params = {"v": dataset_version}
        
        if rejection_reason:
            query += " AND rejection_reason = :reason"
            params["reason"] = rejection_reason
        
        query += " ORDER BY created_at DESC LIMIT :limit"
        params["limit"] = limit
        
        logs = db.execute(text(query), params).fetchall()
        
        return {
            "dataset_version": dataset_version,
            "total_rejections": len(logs),
            "logs": [
                {
                    "row_index": row[0],
                    "rejection_reason": row[1],
                    "organism": row[2],
                    "ward": row[3],
                    "sample_date": str(row[4]) if row[4] else None,
                    "details": row[5],
                    "timestamp": str(row[6])
                }
                for row in logs
            ]
        }
    
    except Exception as e:
        logger.error(f"Quality log error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stp/stage1/descriptive-stats", tags=["STP Surveillance"])
async def get_stp_descriptive_stats(dataset_version: str = "v1.0.0"):
    """
    Get STP descriptive statistics (M3: includes temporal density).
    
    Security: Public (aggregated data only)
    M10: NO resistance rates (Stage 1 firewall)
    """
    try:
        result = compute_descriptive_stats(dataset_version=dataset_version)
        return result
    except Exception as e:
        logger.error(f"Descriptive stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stp/stage1/canonical-data", tags=["STP Surveillance"])
async def export_stp_canonical_data(
    dataset_version: str = "v1.0.0",
    limit: int = 1000,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export STP canonical long-format data.
    
    Security: Requires authentication
    """
    try:
        query = text("""
            SELECT isolate_id, sample_date, organism, ward, sample_type,
                   antibiotic, ast_result
            FROM stp_canonical_long
            WHERE dataset_version = :v
            ORDER BY sample_date DESC, isolate_id
            LIMIT :limit
        """)
        
        rows = db.execute(query, {"v": dataset_version, "limit": limit}).fetchall()
        
        return {
            "dataset_version": dataset_version,
            "record_count": len(rows),
            "data": [
                {
                    "isolate_id": row[0],
                    "sample_date": str(row[1]),
                    "organism": row[2],
                    "ward": row[3],
                    "sample_type": row[4],
                    "antibiotic": row[5],
                    "ast_result": row[6]
                }
                for row in rows
            ]
        }
    
    except Exception as e:
        logger.error(f"Data export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/stp/stage1/freeze", tags=["STP Surveillance"])
async def freeze_stp_dataset(
    request: STPFreezeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    M6: Mark a dataset version as FROZEN (immutable).
    
    Frozen datasets cannot be overwritten.
    Requires admin privileges (future enhancement).
    
    Security: Requires authentication
    """
    try:
        # Check if version exists
        check_query = text("SELECT is_frozen FROM stp_dataset_metadata WHERE dataset_version = :v")
        result = db.execute(check_query, {"v": request.dataset_version}).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Dataset version {request.dataset_version} not found")
        
        if result[0]:
            raise HTTPException(status_code=400, detail=f"Dataset {request.dataset_version} is already frozen")
        
        # Freeze the dataset
        freeze_query = text("""
            UPDATE stp_dataset_metadata
            SET is_frozen = TRUE,
                approved_at = NOW(),
                approved_by = :approved_by
            WHERE dataset_version = :v
        """)
        
        db.execute(freeze_query, {"v": request.dataset_version, "approved_by": request.approved_by})
        db.commit()
        
        logger.info(f"🔒 Dataset {request.dataset_version} FROZEN by {request.approved_by}")
        
        return {
            "status": "frozen",
            "dataset_version": request.dataset_version,
            "approved_by": request.approved_by,
            "approved_at": datetime.now(),
            "message": f"Dataset {request.dataset_version} is now immutable (M6)"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Freeze error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# Startup/Shutdown Events
# ============================================


# ============================================
# PHASE 3B — PERFORMANCE SUMMARY ENDPOINT
# ============================================

@app.get("/api/performance/summary")
def get_performance_summary(db: Session = Depends(get_db)):
    """
    Returns per-target rolling performance metrics computed by Phase 3B.

    Each row contains:
      - mae:              Rolling 12-week Mean Absolute Error (%)
      - bias:             Mean signed bias — positive = over-predicting susceptibility
      - mda:              Mean Directional Accuracy (%)
      - validated_count:  Number of validated weeks in the rolling window
      - performance_status:
            EXCELLENT          (MAE ≤ 5%)
            ACCEPTABLE         (MAE ≤ 10%)
            NEEDS_RECAL        (MAE > 10%)
            DEGRADED           (MAE > 12% with ≥ 8 samples — sticky until retrained)
            INSUFFICIENT_DATA  (< 6 validated weeks)
      - degraded:         True if degradation flag is set (sticky)
      - adaptive_ci_half: Half-width of adaptive CI (MAE × 1.96), or 10.0 if insufficient data
    """
    try:
        result = db.execute(text("""
            SELECT
                ward,
                organism,
                antibiotic,
                mae_score,
                mean_bias,
                mda,
                validated_count,
                performance_status,
                degradation_flagged,
                updated_at
            FROM model_performance
            WHERE model_name = 'Phase3B_Rolling'
            ORDER BY ward, organism, antibiotic
        """)).fetchall()

        rows = []
        for r in result:
            validated_count = r[6] or 0
            mae = float(r[3]) if r[3] is not None else None

            # Adaptive CI half-width: MAE × 1.96, fallback ±10% when insufficient data
            adaptive_ci_half = (
                round(float(mae) * 1.96, 2)
                if mae is not None and validated_count >= 6
                else 10.0
            )

            rows.append({
                "ward":              r[0],
                "organism":          r[1],
                "antibiotic":        r[2],
                "mae":               round(mae, 2) if mae is not None else None,
                "bias":              round(float(r[4]), 2) if r[4] is not None else None,
                "mda":               round(float(r[5]), 1) if r[5] is not None else None,
                "validated_count":   validated_count,
                "performance_status":r[7] or "INSUFFICIENT_DATA",
                "degraded":          bool(r[8]) if r[8] is not None else False,
                "adaptive_ci_half":  adaptive_ci_half,
                "updated_at":        r[9].isoformat() if r[9] else None,
            })

        return {
            "total_targets": len(rows),
            "summary": rows
        }

    except Exception as e:
        logger.error(f"Performance summary error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("startup")
async def startup_event():
    """Execute on application startup"""
    logger.info("AST Prediction API starting up...")
    
    # Pre-Load LSTM Model (Hybrid Architecture)
    try:
        logger.info("🧠 Loading Deep Learning Model (LSTM)...")
        app.state.lstm_model = PredictionService.load_lstm_model("/app/models/best_models/lstm_model.pth")
        if app.state.lstm_model:
            logger.info("✅ LSTM Model Loaded Successfully")
        else:
            logger.warning("⚠️ LSTM Model could not be loaded")
    except Exception as e:
        logger.error(f"Failed to load LSTM: {e}")
        app.state.lstm_model = None

    # Test database connection
    if test_connection():
        logger.info("✓ Database connection established")
    else:
        logger.error("✗ Database connection failed")

@app.on_event("shutdown")
async def shutdown_event():
    """Execute on application shutdown"""
    logger.info("AST Prediction API shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
