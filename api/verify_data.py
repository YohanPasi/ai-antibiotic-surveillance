import os
from sqlalchemy import create_engine, text
import json

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("Checking Table Schema...")
    res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'mrsa_risk_assessments'"))
    cols = [r[0] for r in res.fetchall()]
    print(f"Columns: {cols}")

    print("\nChecking Data for ID=1...")
    row = conn.execute(text("SELECT id, risk_band, input_snapshot FROM mrsa_risk_assessments WHERE id = 1")).fetchone()
    if row:
        print(f"ID: {row[0]}")
        print(f"Risk: {row[1]}")
        print(f"Input Snapshot (Raw): {row[2]}")
        if row[2] is None:
            print("ALERT: Input Snapshot is NULL!")
        else:
            print("Snapshot Type:", type(row[2]))
    else:
        print("No record found for ID=1")
