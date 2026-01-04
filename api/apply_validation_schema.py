import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "postgresql://postgres.zdhvyhijuriggezelyxq:Yohan%26pasi80253327@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres?sslmode=require"

def apply_validation_schema():
    print("Applying MRSA Validation Schema (Stage D)...")
    
    # Embedded SQL
    sql_script = """
    CREATE TABLE IF NOT EXISTS mrsa_validation_log (
        id SERIAL PRIMARY KEY,
        assessment_id INTEGER REFERENCES mrsa_risk_assessments(id),

        ward VARCHAR(50),
        sample_type VARCHAR(50),

        cefoxitin_result VARCHAR(10),
        actual_mrsa BOOLEAN,

        rf_band VARCHAR(20),
        lr_band VARCHAR(20),
        xgb_band VARCHAR(20),
        consensus_band VARCHAR(20),
        
        confidence_level VARCHAR(20),
        model_versions JSONB,

        rf_correct BOOLEAN,
        lr_correct BOOLEAN,
        xgb_correct BOOLEAN,
        consensus_correct BOOLEAN,

        validation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_validation_date ON mrsa_validation_log(validation_date);
    CREATE INDEX IF NOT EXISTS idx_validation_correct ON mrsa_validation_log(consensus_correct);
    """
    
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Executing CREATE TABLE...")
        conn.execute(text(sql_script))
        conn.commit()
    
    print("✅ Schema Applied Successfully.")

if __name__ == "__main__":
    apply_validation_schema()
