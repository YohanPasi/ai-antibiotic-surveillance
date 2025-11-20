from fastapi import APIRouter, Query
from sqlalchemy import func
from sqlalchemy.sql import case
from ..db.base import SessionLocal
from ..db.NON_FEM.models_nonfermenter import (
    NonFermenterIsolate,
    NonFermenterAST,
    NonFermenterFeature
)

router = APIRouter(prefix="/nonfermenter", tags=["NonFermenter"])

# ---------------------- Ward Summary ----------------------
@router.get("/ward-summary")
def ward_summary():
    with SessionLocal() as s:
        rows = (s.query(
            NonFermenterIsolate.ward,
            func.count().label("n"),
            func.sum(case((NonFermenterIsolate.carbapenem_resistant == 1, 1), else_=0)).label("cr")
        )
        .group_by(NonFermenterIsolate.ward)
        .all())
        
        result = []
        for ward, total, cr in rows:
            cr = cr or 0
            result.append({
                "ward": ward,
                "total": total,
                "cr": cr,
                "cr_rate": cr / total if total else 0
            })
        return sorted(result, key=lambda x: x["total"], reverse=True)

# ---------------------- Antibiogram ----------------------
@router.get("/antibiogram")
def antibiogram():
    with SessionLocal() as s:
        rows = (s.query(
            NonFermenterAST.antibiotic,
            func.count().label("n"),
            func.sum(case((NonFermenterAST.sir == "R", 1), else_=0)).label("r")
        )
        .group_by(NonFermenterAST.antibiotic)
        .all())
        
        result = []
        for abx, total, r in rows:
            r = r or 0
            result.append({
                "antibiotic": abx,
                "r_rate": r / total if total else 0,
                "total": total
            })
        return result

# ---------------------- Isolates ----------------------
@router.get("/isolates")
def isolates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=5, le=200),
    ward: str = None
):
    offset = (page - 1) * page_size
    with SessionLocal() as s:
        q = s.query(NonFermenterIsolate).order_by(NonFermenterIsolate.id.desc())
        
        if ward:
            q = q.filter(NonFermenterIsolate.ward == ward)
        
        total = q.count()
        rows = q.offset(offset).limit(page_size).all()
        
        items = []
        for r in rows:
            items.append({
                "id": r.id,
                "sample_id": r.sample_id,
                "ward": r.ward,
                "sample_type": r.sample_type,
                "collection_time": r.collection_time,
                "carbapenem_resistant": r.carbapenem_resistant
            })
        
        return {"items": items, "total": total}

# ---------------------- Isolate Detail ----------------------
@router.get("/isolate/{id}")
def isolate_detail(id: int):
    with SessionLocal() as s:
        iso = s.query(NonFermenterIsolate).filter(NonFermenterIsolate.id == id).first()
        if not iso:
            return {"error": "Not found"}
        
        ast = s.query(NonFermenterAST).filter(NonFermenterAST.isolate_id == id).all()
        features = s.query(NonFermenterFeature).filter(NonFermenterFeature.isolate_id == id).all()
        
        return {
            "isolate": {
                "id": iso.id,
                "sample_id": iso.sample_id,
                "ward": iso.ward,
                "sample_type": iso.sample_type,
                "collection_time": iso.collection_time,
                "organism": iso.organism,
                "carbapenem_resistant": iso.carbapenem_resistant
            },
            "ast": [
                {"antibiotic": a.antibiotic, "sir": a.sir} for a in ast
            ],
            "features": [
                {
                    "light_stage": f.light_stage,
                    "ward": f.ward,
                    "sample_type": f.sample_type,
                    "gram": f.gram,
                    "hour_of_day": f.hour_of_day
                }
                for f in features
            ]
        }
