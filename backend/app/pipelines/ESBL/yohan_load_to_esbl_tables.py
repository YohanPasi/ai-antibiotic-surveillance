import pandas as pd
from sqlalchemy.exc import IntegrityError
from app.db.base import SessionLocal, Base, engine
from app.db.ESBL.models_esbl import EsblIsolate, EsblAST, EsblFeatures, EsblPrediction
from app.config import settings
from datetime import datetime
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parents[4] / "data" / "processed" / "yohan" / "yohan_training.csv"

def parse_dt(v):
    try:
        return pd.to_datetime(v, errors="coerce").to_pydatetime()
    except Exception:
        return None

def to_sir(v):
    if pd.isna(v): return None
    s = str(v).strip().upper()
    return s if s in {"S","I","R"} else None

def main():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"File not found: {DATA_FILE}")
    
    # Create tables if they don't exist
    print("Creating ESBL tables if they don't exist...")
    Base.metadata.create_all(bind=engine, tables=[
        EsblIsolate.__table__,
        EsblAST.__table__,
        EsblFeatures.__table__,
        EsblPrediction.__table__,
    ])
    
    df = pd.read_csv(DATA_FILE)
    abx_cols = [c for c in df.columns if c.endswith("_result")]

    print(f"Connecting DB: {settings.db_url}")
    with SessionLocal() as session:
        inserted, skipped = 0, 0
        for _, row in df.iterrows():
            sid = int(row["sample_id"])
            if session.get(EsblIsolate, sid):
                skipped += 1
                continue

            iso = EsblIsolate(
                sample_id=sid,
                patient_key=str(800000 + sid),
                collection_time=parse_dt(row.get("collection_time")),
                ward=row.get("ward"),
                sample_type=row.get("sample_type"),
                gram=row.get("gram"),
                organism=row.get("organism"),
                esbl_label=None,
                created_at=datetime.utcnow()
            )
            session.add(iso)

            for col in abx_cols:
                val = to_sir(row[col])
                if val:
                    session.add(EsblAST(sample_id=sid, antibiotic=col.replace("_result",""), sir=val))

            # Light-1 + Light-4 feature snapshots
            time = parse_dt(row.get("collection_time"))
            hour = time.hour if time else None
            for stage in ["light1","light4"]:
                session.add(EsblFeatures(
                    sample_id=sid, light_stage=stage, ward=row.get("ward"),
                    sample_type=row.get("sample_type"), gram=row.get("gram"), hour_of_day=hour
                ))

            inserted += 1
            if inserted % 200 == 0:
                session.commit()
        session.commit()
    print(f"✅ Inserted {inserted}, skipped {skipped}")

if __name__ == "__main__":
    main()
