from sqlalchemy import create_engine, text
import os

# Use env var from container
DATABASE_URL = os.getenv("DATABASE_URL")

def inspect_data():
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL not found!")
        return

    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            print("\n--- Columns in mrsa_risk_assessments ---")
            # Select 1 row to get keys, or use information_schema
            res = conn.execute(text("SELECT * FROM mrsa_risk_assessments LIMIT 1"))
            print(res.keys())

            print("\n--- Recent Risk Assessments ---")
            # Fallback to no ordering if created_at missing, or use ID
            assessments = conn.execute(text("SELECT * FROM mrsa_risk_assessments ORDER BY id DESC LIMIT 5")).fetchall()
            for r in assessments:
                print(r)

            print("\n--- Recent AST Entries ---")
            entries = conn.execute(text("SELECT id, ward, specimen_type, organism, antibiotic, result, created_at FROM ast_manual_entry ORDER BY created_at DESC LIMIT 10")).fetchall()
            for r in entries:
                 print(f"ID: {r.id}, Ward: '{r.ward}', Specimen: '{r.specimen_type}', Org: '{r.organism}', Abx: '{r.antibiotic}', Res: '{r.result}'")
                 
            print("\n--- Validation Logs ---")
            logs = conn.execute(text("SELECT * FROM mrsa_validation_log ORDER BY validation_date DESC LIMIT 5")).fetchall()
            print(logs)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_data()
