from datetime import datetime, timedelta, date
from typing import List, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.base import SessionLocal
from app.db.models_mrsa import MrsaPrediction

router = APIRouter(prefix="/mrsa/dashboard", tags=["MRSA Dashboard"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --------- Helper: floor a date to Monday (start of week) ----------
def week_start(dt: date) -> date:
    return dt - timedelta(days=dt.weekday())


# ================== 1. Weekly Trend Endpoint =======================
@router.get("/weekly_trend")
def get_weekly_trend(weeks: int = 8, db: Session = Depends(get_db)):
    """
    Returns weekly MRSA prediction trend for the last N weeks.
    Buckets by week_start (Monday), computes:
      - total predictions
      - number predicted MRSA
      - mrsa_rate
      - avg_probability
    """
    try:
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(weeks=weeks)

        # Get all predictions and filter in Python to avoid SQLAlchemy issues
        all_preds = db.query(MrsaPrediction).all()
        preds: List[MrsaPrediction] = [
            p for p in all_preds 
            if p.created_at is not None 
            and p.created_at >= datetime.combine(start_date, datetime.min.time())
        ]
        preds.sort(key=lambda x: x.created_at)

        buckets: Dict[date, Dict[str, float]] = {}

        for p in preds:
            if p.created_at is None:
                continue
            d = p.created_at.date()
            ws = week_start(d)
            if ws not in buckets:
                buckets[ws] = {
                    "total": 0,
                    "mrsa_count": 0,
                    "sum_prob": 0.0,
                }
            buckets[ws]["total"] += 1
            if p.predicted_label == 1:
                buckets[ws]["mrsa_count"] += 1
            prob = float(p.probability) if p.probability is not None else 0.0
            buckets[ws]["sum_prob"] += prob

        # Convert to sorted list
        result = []
        for ws, agg in sorted(buckets.items(), key=lambda x: x[0]):
            total = agg["total"]
            mrsa_count = agg["mrsa_count"]
            avg_prob = agg["sum_prob"] / total if total > 0 else 0.0
            result.append(
                {
                    "week_start": ws.isoformat(),
                    "total": total,
                    "mrsa_count": mrsa_count,
                    "mrsa_rate": mrsa_count / total if total > 0 else 0.0,
                    "avg_probability": avg_prob,
                }
            )

        return {
            "weeks": weeks,
            "from": start_date.isoformat(),
            "to": end_date.isoformat(),
            "points": result,
        }
    except Exception as e:
        return {
            "weeks": weeks,
            "from": start_date.isoformat() if 'start_date' in locals() else "",
            "to": end_date.isoformat() if 'end_date' in locals() else "",
            "points": [],
            "error": str(e)
        }


# ================== 2. Recent Predictions ==========================
@router.get("/recent")
def get_recent_predictions(limit: int = 50, db: Session = Depends(get_db)):
    """
    Returns the most recent predictions for timeline table.
    """
    try:
        # Get all predictions and filter in Python
        all_preds = db.query(MrsaPrediction).all()
        valid_preds = [p for p in all_preds if p.created_at is not None]
        valid_preds.sort(key=lambda x: x.created_at, reverse=True)
        preds = valid_preds[:limit]

        items = []
        for p in preds:
            items.append(
                {
                    "id": p.id,
                    "sample_id": str(p.sample_id) if p.sample_id is not None else None,
                    "ward": p.ward,
                    "sample_type": p.sample_type,
                    "organism": p.organism,
                    "gram": p.gram,
                    "model_type": p.model_type,
                    "probability": float(p.probability) if p.probability is not None else 0.0,
                    "predicted_label": p.predicted_label if p.predicted_label is not None else 0,
                    "created_at": p.created_at.isoformat() if p.created_at else datetime.utcnow().isoformat(),
                }
            )

        return {"count": len(items), "items": items}
    except Exception as e:
        return {"count": 0, "items": [], "error": str(e)}


# ================== 3. High-Risk Alerts ============================
@router.get("/high_risk")
def get_high_risk_alerts(
    threshold: float = 0.8,
    days: int = 14,
    db: Session = Depends(get_db),
):
    """
    Returns predictions with probability >= threshold in the last N days.
    This powers the alert panel on the dashboard.
    """
    try:
        since = datetime.utcnow() - timedelta(days=days)

        # Get all predictions and filter in Python
        all_preds = db.query(MrsaPrediction).all()
        preds = [
            p for p in all_preds
            if p.created_at is not None
            and p.probability is not None
            and p.created_at >= since
            and p.probability >= threshold
        ]
        preds.sort(key=lambda x: x.probability, reverse=True)

        items = []
        for p in preds:
            items.append(
                {
                    "id": p.id,
                    "sample_id": str(p.sample_id) if p.sample_id is not None else None,
                    "ward": p.ward,
                    "sample_type": p.sample_type,
                    "organism": p.organism,
                    "gram": p.gram,
                    "model_type": p.model_type,
                    "probability": float(p.probability) if p.probability is not None else 0.0,
                    "predicted_label": p.predicted_label if p.predicted_label is not None else 0,
                    "created_at": p.created_at.isoformat() if p.created_at else datetime.utcnow().isoformat(),
                }
            )

        return {
            "threshold": threshold,
            "days": days,
            "count": len(items),
            "items": items,
        }
    except Exception as e:
        return {
            "threshold": threshold,
            "days": days,
            "count": 0,
            "items": [],
            "error": str(e)
        }
