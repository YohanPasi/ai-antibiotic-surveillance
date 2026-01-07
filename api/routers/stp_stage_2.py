
"""
STP Stage 2: Public API Router
-----------------------------
Read-only endpoints for resistance signals.
GOVERNANCE: M20 (Non-Causal Declaration) - All docs must state these are descriptive signals only.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional

from database import get_db

router = APIRouter(
    prefix="/api/stp/stage2",
    tags=["STP Stage 2 (Resistance Signals)"],
    responses={
        200: {"description": "Success"},
        400: {"description": "Invalid Request"}
    }
)

# M20 Declaration
M20_WARNING = """
**GOVERNANCE M20 WARNING**: 
These signals represent descriptive epidemiological associations and temporal patterns only.
No causal inference regarding antibiotic use, resistance emergence, or transmission dynamics is implied.
"""

@router.get("/wards", response_model=List[str])
def get_active_wards(db: Session = Depends(get_db)):
    """
    Fetch all wards that have resistance data computed in Stage 2.
    """
    try:
        # Query distinct wards from weekly rates table
        query = text("SELECT DISTINCT ward FROM stp_resistance_rates_weekly ORDER BY ward")
        result = db.execute(query).fetchall()
        wards = [row[0] for row in result]
        return wards
    except Exception as e:
        print(f"Error fetching wards: {e}")
        return []

@router.get("/weekly-rates", summary="Weekly Resistance Rates", description=M20_WARNING)
def get_weekly_rates(
    organism: Optional[str] = None,
    antibiotic: Optional[str] = None,
    ward: Optional[str] = None,
    db: Session = Depends(get_db),
    limit: int = 1000
):
    """
    Returns aggregated weekly resistance rates.
    """
    query_str = "SELECT * FROM public.stp_resistance_rates_weekly WHERE 1=1"
    params = {}
    
    if organism:
        query_str += " AND organism = :organism"
        params['organism'] = organism
    if antibiotic:
        query_str += " AND antibiotic = :antibiotic"
        params['antibiotic'] = antibiotic
    if ward:
        query_str += " AND ward = :ward"
        params['ward'] = ward
        
    query_str += " ORDER BY week_start DESC LIMIT :limit"
    params['limit'] = limit
    
    result = db.execute(text(query_str), params)
    return [dict(row._mapping) for row in result]

@router.get("/monthly-rates", summary="Monthly Resistance Rates", description=M20_WARNING)
def get_monthly_rates(
    organism: Optional[str] = None,
    antibiotic: Optional[str] = None,
    ward: Optional[str] = None,
    db: Session = Depends(get_db),
    limit: int = 1000
):
    """
    Returns aggregated monthly resistance rates.
    """
    query_str = "SELECT * FROM public.stp_resistance_rates_monthly WHERE 1=1"
    params = {}
    
    if organism:
        query_str += " AND organism = :organism"
        params['organism'] = organism
    if antibiotic:
        query_str += " AND antibiotic = :antibiotic"
        params['antibiotic'] = antibiotic
    if ward:
        query_str += " AND ward = :ward"
        params['ward'] = ward
        
    query_str += " ORDER BY month_start DESC LIMIT :limit"
    params['limit'] = limit
    
    result = db.execute(text(query_str), params)
    return [dict(row._mapping) for row in result]

@router.get("/ward-profile", summary="Ward Resistance Profiles", description=M20_WARNING)
def get_ward_profiles(
    ward: Optional[str] = None,
    organism: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Returns static resistance fingerprints for wards.
    """
    query_str = "SELECT * FROM public.stp_ward_resistance_profile WHERE 1=1"
    params = {}
    
    if ward:
        query_str += " AND ward = :ward"
        params['ward'] = ward
    if organism:
        query_str += " AND organism = :organism"
        params['organism'] = organism
        
    result = db.execute(text(query_str), params)
    return [dict(row._mapping) for row in result]

@router.get("/trends", summary="Temporal Trends & Volatility", description=M20_WARNING)
def get_trends(
    organism: Optional[str] = None,
    ward: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Returns trend slopes and volatility metrics.
    """
    query_str = "SELECT * FROM public.stp_temporal_trend_signals WHERE 1=1"
    params = {}
    
    if organism:
        query_str += " AND organism = :organism"
        params['organism'] = organism
    if ward:
        query_str += " AND ward = :ward"
        params['ward'] = ward
        
    query_str += " ORDER BY week_start DESC LIMIT 1000"
    result = db.execute(text(query_str), params)
    return [dict(row._mapping) for row in result]

@router.get("/feature-store", summary="Stage 2 Feature Store (ML Input)", description=M20_WARNING + "\n\n**STRICT ACCESS**: Input for Stage 3 ML only.")
def get_feature_store(
    version: Optional[str] = None,
    db: Session = Depends(get_db),
    limit: int = 100
):
    """
    Access point for frozen feature snapshots.
    """
    query_str = "SELECT * FROM public.stp_stage2_feature_store WHERE 1=1"
    params = {}
    
    if version:
        query_str += " AND stage2_version = :version"
        params['version'] = version
        
    query_str += " ORDER BY week_start DESC LIMIT :limit"
    params['limit'] = limit
    
    result = db.execute(text(query_str), params)
    return [dict(row._mapping) for row in result]
