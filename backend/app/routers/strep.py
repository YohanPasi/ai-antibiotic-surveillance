from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..db.base import get_db
from ..db.STREP.models_strep import StrepIsolate, StrepAST

router = APIRouter(prefix="/strep", tags=["Streptococcus"])


# Convert isolate → JSON
def serialize_isolate(i: StrepIsolate):
    return {
        "id": i.id,
        "sample_id": i.sample_id,
        "patient_id": i.patient_id,
        "organism": i.organism,
        "sample_type": i.sample_type,
        "ward": i.ward,
        "sex": i.sex,
        "age": i.age,
        "collection_time": i.collection_time.isoformat() if i.collection_time else None,
    }


def serialize_ast(a: StrepAST):
    return {
        "antibiotic": a.antibiotic,
        "result": a.result
    }


# ----------------------------------------------------------
# GET /strep/isolates → Paginated list + filters
# ----------------------------------------------------------
@router.get("/isolates")
def get_isolates(
    page: int = 1,
    page_size: int = 20,
    ward: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(StrepIsolate)

    if ward:
        query = query.filter(StrepIsolate.ward == ward)

    total = query.count()

    items = (
        query.order_by(StrepIsolate.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "items": [serialize_isolate(i) for i in items],
        "total": total
    }


# ----------------------------------------------------------
# GET /strep/isolate/{id} → Full isolate + AST + features
# ----------------------------------------------------------
@router.get("/isolate/{isolate_id}")
def get_isolate(isolate_id: int, db: Session = Depends(get_db)):
    iso = db.query(StrepIsolate).filter(StrepIsolate.id == isolate_id).first()
    if not iso:
        return {"error": "Not found"}

    ast = db.query(StrepAST).filter(StrepAST.isolate_id == iso.id).all()

    return {
        "isolate": serialize_isolate(iso),
        "ast": [serialize_ast(a) for a in ast],
        "features": [
            {
                "light_stage": "meta",
                "ward": iso.ward,
                "sample_type": iso.sample_type,
                "gram": "Gram+",
                "hour_of_day": iso.collection_time.hour if iso.collection_time else None,
            }
        ],
    }


# ----------------------------------------------------------
# GET /strep/ward-summary → Cases per ward + positivity rate
# ----------------------------------------------------------
@router.get("/ward-summary")
def ward_summary(db: Session = Depends(get_db)):
    rows = db.query(StrepIsolate).all()

    summary = {}
    for r in rows:
        w = r.ward or "Unknown"
        if w not in summary:
            summary[w] = {"ward": w, "total": 0}
        summary[w]["total"] += 1

    return list(summary.values())


# ----------------------------------------------------------
# GET /strep/antibiogram → % Resistance by antibiotic
# ----------------------------------------------------------
@router.get("/antibiogram")
def antibiogram(db: Session = Depends(get_db)):

    ast_rows = db.query(StrepAST).all()

    stats = {}
    for a in ast_rows:
        abx = a.antibiotic
        if abx not in stats:
            stats[abx] = {"antibiotic": abx, "total": 0, "r": 0}
        stats[abx]["total"] += 1
        if a.result.upper() == "R":
            stats[abx]["r"] += 1

    output = []
    for abx, d in stats.items():
        output.append({
            "antibiotic": abx,
            "r_rate": d["r"] / d["total"] if d["total"] else 0
        })

    return output
