from fastapi import APIRouter, Query
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import case
from ..db.base import SessionLocal
from ..db.ESBL.models_esbl import EsblIsolate, EsblAST, EsblFeatures

router = APIRouter(prefix="/esbl", tags=["ESBL"])

@router.get("/isolates")
def list_isolates(page: int = 1, page_size: int = 20, ward: str | None = None):
    offset = (page - 1) * page_size
    with SessionLocal() as s:
        q = s.query(EsblIsolate).order_by(EsblIsolate.collection_time.desc())
        if ward:
            q = q.filter(EsblIsolate.ward == ward)
        total = q.count()
        rows = (q.options(joinedload(EsblIsolate.ast))
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
                    "organism": r.organism,
                    "esbl_label": r.esbl_label,
                } for r in rows
            ]
        }

@router.get("/ward_summary")
def ward_summary():
    with SessionLocal() as s:
        rows = (s.query(EsblIsolate.ward,
                        func.count().label("n"),
                        func.sum(case((EsblIsolate.esbl_label == True, 1), else_=0)).label("n_esbl"))
                  .group_by(EsblIsolate.ward)
                  .all())
        out = []
        for w, n, n_esbl in rows:
            n_esbl = n_esbl or 0
            out.append({"ward": w, "total": n, "esbl": n_esbl, "esbl_rate": (n_esbl / n) if n else 0})
        return sorted(out, key=lambda x: x["total"], reverse=True)

@router.get("/antibiogram")
def antibiogram():
    with SessionLocal() as s:
        rows = (s.query(EsblAST.antibiotic,
                        func.count().label("n"),
                        func.sum(case((EsblAST.sir == "R", 1), else_=0)).label("r"))
                  .group_by(EsblAST.antibiotic)
                  .all())
        return [{"antibiotic": abx, "r_rate": (r or 0) / n if n else 0} for abx, n, r in rows]

@router.get("/isolate/{sample_id}")
def isolate_detail(sample_id: int):
    with SessionLocal() as s:
        iso = s.get(EsblIsolate, sample_id)
        if not iso:
            return {"error": "not found"}
        ast = s.query(EsblAST).filter(EsblAST.sample_id == sample_id).all()
        feats = s.query(EsblFeatures).filter(EsblFeatures.sample_id == sample_id).all()
        return {
            "isolate": {
                "sample_id": iso.sample_id,
                "ward": iso.ward,
                "sample_type": iso.sample_type,
                "collection_time": iso.collection_time,
                "organism": iso.organism,
                "gram": iso.gram,
                "esbl_label": iso.esbl_label,
            },
            "ast": [{"antibiotic": a.antibiotic, "sir": a.sir} for a in ast],
            "features": [
                {"light_stage": f.light_stage, "ward": f.ward,
                 "sample_type": f.sample_type, "gram": f.gram,
                 "hour_of_day": f.hour_of_day}
                for f in feats
            ]
        }
