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

# Configure CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
# API Endpoints
# ============================================

@app.post("/api/entry")
async def create_ast_entry(entry: ASTPanelEntry, background_tasks: BackgroundTasks):
    """
    Manual AST Data Entry Endpoint (Panel/Collection).
    Saves raw data and triggers the Learning Loop.
    """
    db = SessionLocal()
    try:
        # 1. SQL Query
        query = text("""
            INSERT INTO esbl_lab_results (
                encounter_id, lab_no, age, gender, bht, ward, specimen_type, organism, antibiotic, result
            ) VALUES (
                :enc_id, :lab, :age, :gen, :bht, :ward, :spec, :org, :abx, :res
            )
        """)
        
        # 2. Iterate Collection and Insert
        for item in entry.results:
            db.execute(query, {
                "enc_id": entry.lab_no,  # Use lab_no as encounter link
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

        db.commit()
        
        # 4. Trigger Background Pipeline ("Stage E" Prep)
        background_tasks.add_task(trigger_pipeline_update)
        
        return {"status": "success", "message": f"Panel saved ({len(entry.results)} results). AI Pipeline triggered."}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Entry Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/options", response_model=OptionsResponse)
async def get_available_options():
    """
    Get available filter options (wards, organisms, antibiotics).
    """
    try:
        db = SessionLocal()
        
        # Get distinct values from database
        wards_query = """
            SELECT DISTINCT ward FROM ast_weekly_aggregated 
            WHERE ward IS NOT NULL ORDER BY ward
        """
        organisms_query = """
            SELECT DISTINCT organism FROM ast_weekly_aggregated 
            ORDER BY organism
        """
        antibiotics_query = """
            SELECT DISTINCT antibiotic FROM ast_weekly_aggregated 
            ORDER BY antibiotic
        """
        
        wards = [row[0] for row in db.execute(text(wards_query)).fetchall()]
        organisms = [row[0] for row in db.execute(text(organisms_query)).fetchall()]
        antibiotics = [row[0] for row in db.execute(text(antibiotics_query)).fetchall()]
        
        db.close()
        
        return OptionsResponse(
            wards=wards if wards else ["ICU", "Ward A", "Ward B"],  # Fallback for demo
            organisms=organisms if organisms else ["Pseudomonas aeruginosa", "Acinetobacter spp.", "Escherichia coli"],
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
        # 1. Fetch History (Last 12 weeks)
        query = """
            SELECT week_start_date, susceptible_count, total_tested
            FROM ast_weekly_aggregated
            WHERE ward = :ward AND organism = :organism AND antibiotic = :antibiotic
            ORDER BY week_start_date ASC
            LIMIT 12
        """
        results = db.execute(text(query), {
            "ward": ward, "organism": organism, "antibiotic": antibiotic
        }).fetchall()
        
        history = []
        s_values = []
        
        for row in results:
            total = row[2]
            s_percent = (row[1] / total * 100.0) if total > 0 else 0.0
            history.append({
                "week": row[0].strftime("%Y-W%U"),
                "date": row[0].strftime("%b %d"),
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
                
             # Create Forecast Object
             last_date = datetime.strptime(history[-1]["date"] + f" {datetime.now().year}", "%b %d %Y") # Approx
             next_date = last_date + timedelta(days=7)
             
             forecast = {
                 "week": "Next Week",
                 "date": "Next Week", # Simplified for UI
                 "predicted_s": round(pred_value, 1)
             }
             
             # Calculate Status for this specific target
             # Using the logic from prediction_service (simplified here for display)
             baseline_val = baseline[-1]["expected_s"]
             alert_status, _, _ = PredictionService.get_hybrid_status(
                 observed_s=s_values[-1],
                 baseline_lower=baseline_val - 10, # Approximate lower bound
                 lstm_forecast=pred_value
             )
             status = alert_status.upper()
             
             _, domain = PredictionService.generate_detailed_stewardship(alert_status, organism, antibiotic, ward)

        return {
            "ward": ward,
            "organism": organism,
            "antibiotic": antibiotic,
            "history": history,
            "baseline": baseline,
            "forecast": forecast,
            "status": status,
            "stewardship_domain": domain,
            "engine_version": "Hybrid_LSTM_v1"
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
                "highest_severity": "Critical" if row[3] > 0 else "Warning" if row[2] > 0 else "Stable"
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
                 WHERE ward = :ward
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
                "trend": trend
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
    Returns both Current Observed S% and Next-Week Predicted S%.
    """
    db = SessionLocal()
    try:
        # Filter by Ward if provided, otherwise Hospital-Wide (Average)
        where_clause = "WHERE ward = :ward" if ward else "WHERE 1=1"
        
        # 1. Fetch raw logs (last 4 entries per target) to build sparklines
        query_history = f"""
            WITH LatestLogs AS (
                 SELECT ward, organism, antibiotic, observed_s_percent, predicted_s_percent, log_date,
                        ROW_NUMBER() OVER(PARTITION BY ward, organism, antibiotic ORDER BY log_date DESC) as rn
                 FROM surveillance_logs
                 {where_clause}
            )
            SELECT organism, antibiotic, observed_s_percent, predicted_s_percent
            FROM LatestLogs
            WHERE rn <= 12
            ORDER BY organism, antibiotic, log_date ASC
        """
        
        params = {"ward": ward} if ward else {}
        raw_rows = db.execute(text(query_history), params).fetchall()
        
        # 2. Aggregate in Python
        # Structure: matrix[org][abx] = { history: [], current: float, predicted: float }
        matrix = {}
        antibiotics_set = set()
        temp_agg = {} # Key: (org, abx) -> { obs_vals: [], pred_vals: [] }

        for row in raw_rows:
            org, abx, obs, pred = row
            antibiotics_set.add(abx)
            key = (org, abx)
            
            if key not in temp_agg:
                temp_agg[key] = {'obs': [], 'pred': []}
            
            if obs is not None: temp_agg[key]['obs'].append(float(obs))
            if pred is not None: temp_agg[key]['pred'].append(float(pred))
            
        # 3. Build Final Matrix
        for (org, abx), vals in temp_agg.items():
            if org not in matrix: matrix[org] = {}
            
            obs_list = vals['obs']
            pred_list = vals['pred']
            
            # Weighted Average (giving more weight to recent?) - For now just simple Average
            current_avg = sum(obs_list) / len(obs_list) if obs_list else 0.0
            predicted_avg = sum(pred_list) / len(pred_list) if pred_list else 0.0
            
            matrix[org][abx] = {
                "current": round(current_avg, 1),
                "predicted": round(predicted_avg, 1),
                "history": obs_list[-4:] # Send last 4 points for sparkline
            }
            
        return {
            "matrix": matrix,
            "antibiotics": sorted(list(antibiotics_set)),
            "scope": f"Ward {ward}" if ward else "Hospital-Wide"
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
