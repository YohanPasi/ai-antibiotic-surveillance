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
            INSERT INTO ast_manual_entry (
                lab_no, age, gender, bht, ward, specimen_type, organism, antibiotic, result
            ) VALUES (
                :lab, :age, :gen, :bht, :ward, :spec, :org, :abx, :res
            )
        """)
        
        # 2. Iterate Collection and Insert
        for item in entry.results:
            db.execute(query, {
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

@app.get("/api/esbl/audit-logs")
async def get_esbl_audit_logs():
    """
    Fetch ESBL Governance Logs (JSONL).
    """
    logs = []
    log_file = "esbl_audit_log.jsonl"
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            for line in f:
                try:
                    logs.append(json.loads(line.strip()))
                except:
                    continue
    return logs.reverse() or logs # Return newest first if possible, or handle in UI

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
