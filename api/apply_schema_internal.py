import os
import sqlalchemy
from sqlalchemy import create_engine, text

# Get URL from environment (Container's context)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("FATAL: DATABASE_URL not set in environment!")
    exit(1)

print(f"Connecting to: {DATABASE_URL.split('@')[-1]}") # Log host only for safety

def apply_schema():
    engine = create_engine(DATABASE_URL)
    
    # Inline SQL to avoid path mapping issues
    sql = """
    DROP TABLE IF EXISTS mrsa_risk_assessments CASCADE;

    CREATE TABLE IF NOT EXISTS mrsa_risk_assessments (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        -- Clinical Context
        ward VARCHAR(50),
        sample_type VARCHAR(50),
        
        -- Prediction Result
        mrsa_probability FLOAT,
        risk_band VARCHAR(10), -- GREEN, AMBER, RED
        model_version VARCHAR(50),
        
        -- Critical for Explainability
        input_snapshot JSONB -- Stores the exact input used for this prediction
    );

    CREATE INDEX IF NOT EXISTS idx_mrsa_risk_timestamp ON mrsa_risk_assessments(timestamp);
    """

    print("Executing Schema Update...")
    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()
    print("✅ Schema applied successfully from INSIDE container.")
    
    # Verify
    print("Verifying columns...")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'mrsa_risk_assessments';"))
        columns = [row[0] for row in result.fetchall()]
        print(f"Current Columns: {columns}")
        if 'input_snapshot' in columns:
            print("VERIFICATION PASSED: input_snapshot exists.")
        else:
            print("VERIFICATION FAILED: input_snapshot missing!")

if __name__ == "__main__":
    apply_schema()
