# backend/app/routers/mrsa.py
from fastapi import APIRouter, Query
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload
from ..db.base import SessionLocal
from ..db.models_mrsa import MrsaIsolate, MrsaAST, MrsaFeatures

router = APIRouter(prefix="/mrsa", tags=["MRSA"])

@router.get("/isolates")
def list_isolates(page: int = 1, page_size: int = 20, ward: str | None = None):
    offset = (page - 1) * page_size
    with SessionLocal() as s:
        q = s.query(MrsaIsolate).order_by(MrsaIsolate.collection_time.desc())
        if ward:
            q = q.filter(MrsaIsolate.ward == ward)
        total = q.count()
        rows = (q.options(joinedload(MrsaIsolate.ast))
                  .offset(offset).limit(page_size).all())
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [
                {
                    "sample_id": r.sample_id,
                    "ward": r.ward,
                    "sample_type": r.sample_type,
                    "collection_time": r.collection_time,
                    "mrsa_label": r.mrsa_label,
                    "organism": r.organism,
                } for r in rows
            ]
        }

@router.get("/isolate/{sample_id}")
def isolate_detail(sample_id: int):
    with SessionLocal() as s:
        iso = s.get(MrsaIsolate, sample_id)
        if not iso:
            return {"error": "not found"}
        ast = s.query(MrsaAST).filter(MrsaAST.sample_id == sample_id).all()
        feats = s.query(MrsaFeatures).filter(MrsaFeatures.sample_id == sample_id).all()
        return {
            "isolate": {
                "sample_id": iso.sample_id,
                "ward": iso.ward,
                "sample_type": iso.sample_type,
                "collection_time": iso.collection_time,
                "mrsa_label": iso.mrsa_label,
                "organism": iso.organism,
                "mecA": iso.mecA,
            },
            "ast": [{"antibiotic": a.antibiotic, "sir": a.sir} for a in ast],
            "features": [{
                "light_stage": f.light_stage,
                "ward": f.ward,
                "sample_type": f.sample_type,
                "gram": f.gram,
                "hour_of_day": f.hour_of_day,
            } for f in feats]
        }

@router.get("/summary/ward")
def ward_summary():
    from sqlalchemy.sql import case
    with SessionLocal() as s:
        rows = (s.query(MrsaIsolate.ward,
                        func.count().label("n"),
                        func.sum(case((MrsaIsolate.mrsa_label == True, 1), else_=0)).label("n_mrsa"))
                  .group_by(MrsaIsolate.ward)
                  .all())
        out = []
        for w, n, n_mrsa in rows:
            n_mrsa = n_mrsa or 0
            out.append({"ward": w, "total": n, "mrsa": n_mrsa, "mrsa_rate": (n_mrsa / n) if n else 0})
        return sorted(out, key=lambda x: x["total"], reverse=True)

@router.get("/summary/antibiogram")
def antibiogram():
    from sqlalchemy.sql import case
    # Percent R per antibiotic (simple)
    with SessionLocal() as s:
        rows = (s.query(MrsaAST.antibiotic,
                        func.count().label("n"),
                        func.sum(case((MrsaAST.sir == "R", 1), else_=0)).label("r"))
                  .group_by(MrsaAST.antibiotic)
                  .all())
        return [{"antibiotic": abx, "tests": n, "r_count": r or 0, "r_rate": (r or 0) / n} for abx, n, r in rows]
