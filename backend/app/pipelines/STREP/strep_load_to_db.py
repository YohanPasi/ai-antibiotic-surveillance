import pandas as pd
from app.db.base import SessionLocal
from app.db.STREP.models_strep import StrepIsolate, StrepAST
from pathlib import Path
from datetime import datetime

# Get project root (4 levels up from this file: STREP -> pipelines -> app -> backend -> project_root)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "strep" / "strep_clean.csv"

def load_strep():
    print("Loading cleaned Strep file...")
    df = pd.read_csv(DATA_PATH)

    db = SessionLocal()

    for _, row in df.iterrows():
        iso = StrepIsolate(
            sample_id=row["sample_id"],
            patient_id=row.get("patient_id"),
            organism=row["organism"],
            sample_type=row["sample_type"],
            ward=row["ward"],
            age=row.get("age"),
            sex=row.get("sex"),
            collection_time=pd.to_datetime(row.get("collection_time"), errors="coerce") if pd.notna(row.get("collection_time")) else None
        )

        db.add(iso)
        db.flush()     # gives isolate ID

        for abx in ["penicillin", "erythromycin", "clindamycin", 
                    "ceftriaxone", "vancomycin", "linezolid"]:

            val = row.get(abx)
            if pd.notna(val):
                db.add(StrepAST(
                    isolate_id=iso.id,
                    antibiotic=abx,
                    result=str(val)
                ))

    db.commit()
    db.close()
    print("Strep data inserted into DB.")


if __name__ == "__main__":
    load_strep()
