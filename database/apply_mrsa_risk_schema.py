import os
from sqlalchemy import create_engine, text

# Supabase Connection String
DATABASE_URL = "postgresql://postgres.zdhvyhijuriggezelyxq:Yohan%26pasi80253327@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres?sslmode=require"

def apply_schema():
    print("Connecting to Supabase...")
    engine = create_engine(DATABASE_URL)
    
    schema_path = r'd:\Yohan\Project\database\create_mrsa_risk_schema.sql'
    
    with open(schema_path, 'r') as f:
        sql = f.read()

    print("Applying Schema...")
    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()
    print("Schema applied successfully to Supabase.")

if __name__ == "__main__":
    apply_schema()
