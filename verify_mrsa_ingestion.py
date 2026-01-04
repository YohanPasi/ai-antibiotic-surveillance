import pandas as pd
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres.zdhvyhijuriggezelyxq:Yohan%26pasi80253327@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres?sslmode=require"

def verify():
    print("Verifying MRSA Stage A Data in Supabase...")
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # 1. Total Count
        result = conn.execute(text("SELECT COUNT(*) FROM mrsa_raw_clean")).scalar()
        print(f"Total Records: {result}")
        
        # 2. Class Distribution
        dist = pd.read_sql("SELECT mrsa_label, COUNT(*) as count FROM mrsa_raw_clean GROUP BY mrsa_label", conn)
        print("\nClass Distribution:")
        print(dist)
        
        # 3. Leakage Check (Column Schema)
        cols = pd.read_sql("SELECT column_name FROM information_schema.columns WHERE table_name = 'mrsa_raw_clean'", conn)
        col_list = cols['column_name'].tolist()
        forbidden = ['cefoxitin', 'vancomycin', 'cloxacillin', 'penicillin', 'result', 'antibiotic']
        leaks = [c for c in col_list if any(f in c.lower() for f in forbidden)]
        
        if leaks:
            print(f"LEAKAGE DETECTED: Found forbidden columns: {leaks}")
        else:
            print("Leakage Check Passed: No antibiotic columns found.")
            
        # 4. Scope Check (Implicit by label existence, but let's check nulls)
        nulls = conn.execute(text("SELECT COUNT(*) FROM mrsa_raw_clean WHERE mrsa_label IS NULL")).scalar()
        if nulls == 0:
            print("Scope Check Passed: All records validly labeled.")
        else:
            print(f"Scope Error: {nulls} records have NULL labels.")

if __name__ == "__main__":
    verify()
