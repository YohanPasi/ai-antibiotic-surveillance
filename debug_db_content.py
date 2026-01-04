from sqlalchemy import create_engine, text
import os

# Database URL (assuming default from docker-compose or env)
# If running locally outside docker, might need localhost. 
# User is running via docker-compose usually, but I am editing files.
# I will assume the script runs in the same env or I can use the one from main.py if I knew it.
# Use env var from container
DATABASE_URL = os.getenv("DATABASE_URL")

def inspect_data():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("\n--- Recent Risk Assessments ---")
        assessments = conn.execute(text("SELECT id, ward, sample_type, created_at, risk_band FROM mrsa_risk_assessments ORDER BY created_at DESC LIMIT 5")).fetchall()
        for r in assessments:
            print(f"ID: {r.id}, Ward: '{r.ward}', Sample: '{r.sample_type}', Time: {r.created_at}, Band: {r.risk_band}")

        print("\n--- Recent AST Entries ---")
        entries = conn.execute(text("SELECT id, ward, specimen_type, organism, antibiotic, result, created_at FROM ast_manual_entry ORDER BY created_at DESC LIMIT 10")).fetchall()
        for r in entries:
             print(f"ID: {r.id}, Ward: '{r.ward}', Specimen: '{r.specimen_type}', Org: '{r.organism}', Abx: '{r.antibiotic}', Res: '{r.result}'")
             
        print("\n--- Validation Logs ---")
        logs = conn.execute(text("SELECT * FROM mrsa_validation_log ORDER BY validation_date DESC LIMIT 5")).fetchall()
        print(logs)

if __name__ == "__main__":
    inspect_data()
