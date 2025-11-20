import pandas as pd
from datetime import datetime
from app.db.base import SessionLocal
from app.db.NON_FEM.models_nonfermenter import (
    NonFermenterIsolate,
    NonFermenterAST,
    NonFermenterFeature
)

CSV_PATH = r"E:\SLIIT\SLIIT STUDY\Y4S1\Research\AI DRIVEN RESEARCH JAYATH\ai-antibiotic-surveillance\data\processed\nonfermenter\nonfermenter_clean.csv"

def load_nonfermenter_data():
    print("Loading CSV:", CSV_PATH)

    df = pd.read_csv(CSV_PATH)
    db = SessionLocal()

    for _, row in df.iterrows():
        isolate = NonFermenterIsolate(
            sample_id=row.get("sample_id"),
            patient_id=row.get("patient_id"),
            organism=row.get("organism"),
            ward=row.get("ward"),
            sample_type=row.get("sample_type"),
            collection_time=pd.to_datetime(row.get("collection_time"), errors="coerce"),
            gram=row.get("gram"),

            meropenem=row.get("meropenem"),
            imipenem=row.get("imipenem"),
            ceftazidime=row.get("ceftazidime"),
            cefepime=row.get("cefepime"),
            amikacin=row.get("amikacin"),
            gentamicin=row.get("gentamicin"),
            tobramycin=row.get("tobramycin"),
            ciprofloxacin=row.get("ciprofloxacin"),
            colistin=row.get("colistin"),

            carbapenem_resistant=int(row.get("carbapenem_resistant"))
        )
        db.add(isolate)
        db.flush()

        # AST rows
        for abx in [
            "meropenem","imipenem","ceftazidime","cefepime","amikacin",
            "gentamicin","tobramycin","ciprofloxacin","colistin"
        ]:
            val = row.get(abx)
            if pd.isna(val): continue

            db.add(NonFermenterAST(
                isolate_id=isolate.id,
                antibiotic=abx,
                sir=val
            ))

        # Feature rows (Light #1 & Light #4)
        db.add(NonFermenterFeature(
            isolate_id=isolate.id,
            light_stage="light1",
            ward=isolate.ward,
            sample_type=isolate.sample_type,
            gram=None,
            hour_of_day=isolate.collection_time.hour if isolate.collection_time else None
        ))

        db.add(NonFermenterFeature(
            isolate_id=isolate.id,
            light_stage="light4",
            ward=isolate.ward,
            sample_type=isolate.sample_type,
            gram=isolate.gram,
            hour_of_day=isolate.collection_time.hour if isolate.collection_time else None
        ))

    db.commit()
    db.close()
    print("Data loaded successfully.")


if __name__ == "__main__":
    load_nonfermenter_data()
