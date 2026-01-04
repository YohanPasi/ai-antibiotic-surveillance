import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "postgresql://postgres.zdhvyhijuriggezelyxq:Yohan%26pasi80253327@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres?sslmode=require"

def apply_schema():
    print("Applying MRSA Risk Assessment Schema Updates (Stage C.5)...")
    
    # Embedded SQL to avoid file path issues in container
    sql_script = """
    -- Add columns to mrsa_risk_assessments for multi-model storage
    ALTER TABLE mrsa_risk_assessments
    ADD COLUMN IF NOT EXISTS rf_probability FLOAT,
    ADD COLUMN IF NOT EXISTS rf_risk_band VARCHAR(50),
    ADD COLUMN IF NOT EXISTS rf_version VARCHAR(50),

    ADD COLUMN IF NOT EXISTS lr_probability FLOAT,
    ADD COLUMN IF NOT EXISTS lr_risk_band VARCHAR(50),
    ADD COLUMN IF NOT EXISTS lr_version VARCHAR(50),

    ADD COLUMN IF NOT EXISTS xgb_probability FLOAT,
    ADD COLUMN IF NOT EXISTS xgb_risk_band VARCHAR(50),
    ADD COLUMN IF NOT EXISTS xgb_version VARCHAR(50),

    ADD COLUMN IF NOT EXISTS consensus_band VARCHAR(50),
    ADD COLUMN IF NOT EXISTS confidence_level VARCHAR(50), 
    ADD COLUMN IF NOT EXISTS consensus_version VARCHAR(50);

    -- Index just in case
    CREATE INDEX IF NOT EXISTS idx_risk_confidence ON mrsa_risk_assessments(confidence_level);
    """
            
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        statements = sql_script.split(';')
        for stmt in statements:
            if stmt.strip():
                print(f"Executing: {stmt[:50]}...")
                conn.execute(text(stmt))
                conn.commit()
                
    print("✅ Schema Applied Successfully.")

if __name__ == "__main__":
    apply_schema()
