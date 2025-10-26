# backend/app/pipelines/mrsa_load_to_mrsa_tables.py
from pathlib import Path
from datetime import datetime
import os
import pandas as pd
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from backend.app.db.base import SessionLocal
from backend.app.db.models_mrsa import MrsaIsolate, MrsaAST, MrsaFeatures
from backend.app.config import settings

HERE = Path(__file__).resolve()
# backend/app/pipelines/ -> parents[3] = ai-antibiotic-surveillance
REPO_ROOT = HERE.parents[3] if len(HERE.parents) > 3 else Path.cwd()
DATA_ROOT = Path(os.getenv("DATA_ROOT", REPO_ROOT / "data"))
MRSA_CSV = DATA_ROOT / "processed" / "mrsa" / "mrsa_training.csv"

ABX_COLUMNS = {
    "cefoxitin_result": "Cefoxitin",
    "oxacillin_result": "Oxacillin",
    "vancomycin_result": "Vancomycin",
    "linezolid_result": "Linezolid",
    "daptomycin_result": "Daptomycin",
    "clindamycin_result": "Clindamycin",
    "erythromycin_result": "Erythromycin",
    "tmpsmx_result": "Trimethoprim/Sulfamethoxazole",
    "tetracycline_result": "Tetracycline",
}

def parse_dt(val):
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d", "%d/%m/%Y %H:%M", "%d/%m/%Y", "%m/%d/%Y %H:%M", "%m/%d/%Y"):
        try:
            return datetime.strptime(str(val), fmt)
        except Exception:
            pass
    try:
        return pd.to_datetime(val, errors="coerce").to_pydatetime()
    except Exception:
        return None

def to_bool(v):
    if pd.isna(v): return None
    s = str(v).strip().lower()
    if s in ("1","true","yes","y"): return True
    if s in ("0","false","no","n"): return False
    return None

def to_sir(v):
    if pd.isna(v): return None
    s = str(v).strip().upper()
    return s if s in {"S","I","R"} else None

def ensure_isolate(session, row):
    # sample_id
    sid = int(row["sample_id"])
    exists = session.get(MrsaIsolate, sid)
    if exists:
        return exists

    # patient key (string OK). If missing, stable pseudo from sample_id
    pid = row.get("patient_id")
    if pd.isna(pid) or pid in ("", None):
        patient_key = str(900000 + sid)
    else:
        patient_key = str(pid)

    iso = MrsaIsolate(
        sample_id=sid,
        patient_key=patient_key,
        collection_time=parse_dt(row.get("collection_time")),
        ward=row.get("ward"),
        sample_type=row.get("sample_type"),
        gram=row.get("gram"),
        organism=row.get("organism") or "Staphylococcus aureus",
        mrsa_label=to_bool(row.get("mrsa_label")) if str(row.get("mrsa_label")).lower() not in ("s","i","r") else None,
        mecA=to_bool(row.get("meca")) if "meca" in row.index else None,
    )
    session.add(iso)
    return iso

def upsert_ast(session, sample_id, df_row):
    for col, pretty in ABX_COLUMNS.items():
        if col not in df_row.index:
            continue
        sir = to_sir(df_row[col])
        if not sir:
            continue
        # unique per (sample_id, antibiotic)
        exists = session.scalar(
            select(MrsaAST.id).where(MrsaAST.sample_id == sample_id, MrsaAST.antibiotic == pretty)
        )
        if exists:
            continue
        session.add(MrsaAST(sample_id=sample_id, antibiotic=pretty, sir=sir))

def ensure_features_snapshots(session, sample_id, df_row):
    # light1 (early): ward, sample_type, gram, hour_of_day
    if not session.scalar(select(MrsaFeatures.id).where(MrsaFeatures.sample_id == sample_id, MrsaFeatures.light_stage == "light1")):
        session.add(MrsaFeatures(
            sample_id=sample_id,
            light_stage="light1",
            ward=df_row.get("ward"),
            sample_type=df_row.get("sample_type"),
            gram=df_row.get("gram"),
            hour_of_day=(parse_dt(df_row.get("collection_time")).hour
                         if parse_dt(df_row.get("collection_time")) else None),
        ))
    # light4 (species known): same + organism context
    if not session.scalar(select(MrsaFeatures.id).where(MrsaFeatures.sample_id == sample_id, MrsaFeatures.light_stage == "light4")):
        session.add(MrsaFeatures(
            sample_id=sample_id,
            light_stage="light4",
            ward=df_row.get("ward"),
            sample_type=df_row.get("sample_type"),
            gram=df_row.get("gram"),
            hour_of_day=(parse_dt(df_row.get("collection_time")).hour
                         if parse_dt(df_row.get("collection_time")) else None),
        ))

def main():
    if not MRSA_CSV.exists():
        raise FileNotFoundError(f"MRSA CSV not found at: {MRSA_CSV}")

    df = pd.read_csv(MRSA_CSV)
    if df.empty:
        print("CSV empty; nothing to load.")
        return

    # Keep only S. aureus rows if your extractor didn’t already filter
    if "organism" in df.columns:
        df = df[df["organism"].str.contains("aureus", case=False, na=False)]

    print(f"Connecting DB: {settings.db_url}")
    inserted, skipped = 0, 0
    with SessionLocal() as session:
        for _, row in df.iterrows():
            try:
                iso = ensure_isolate(session, row)
                upsert_ast(session, iso.sample_id, row)
                ensure_features_snapshots(session, iso.sample_id, row)
                inserted += 1
                if inserted % 200 == 0:
                    session.commit()
            except IntegrityError:
                session.rollback()
                skipped += 1
            except Exception as e:
                session.rollback()
                print(f"Row failed (Sample_ID={row.get('sample_id')}): {e}")
                skipped += 1
        session.commit()

    print(f"MRSA upsert complete. Rows touched ~{inserted}; skipped {skipped}.")

if __name__ == "__main__":
    main()
