import requests
import time
from sqlalchemy import create_engine, text
import os

# Database Config (Internal Docker Network)
DATABASE_URL = "postgresql://ast_user:secure_password@db:5432/ast_db"
API_URL = "http://localhost:8000/api/predict"

def main():
    print("="*60)
    print("🏥 STARTING HOSPITAL-WIDE SURVEILLANCE SWEEP")
    print("="*60)

    # 1. Connect to DB to get Targets
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            query = """
                SELECT DISTINCT ward, organism, antibiotic 
                FROM ast_weekly_aggregated
                WHERE total_tested >= 10 -- Minimum threshold for validity
            """
            result = conn.execute(text(query)).fetchall()
            targets = [row for row in result]
            
        print(f"✅ Found {len(targets)} unique targets (Ward/Bug/Drug) to analyze.")
        
    except Exception as e:
        print(f"❌ Database Connection Error: {e}")
        return

    # 2. Iterate and Trigger Prediction
    success_count = 0
    error_count = 0
    
    start_time = time.time()
    
    for i, (ward, organism, antibiotic) in enumerate(targets):
        payload = {
            "ward": ward,
            "organism": organism,
            "antibiotic": antibiotic
        }
        
        try:
            # We use localhost because we'll run this inside the container 
            # where API is on port 8000 locally? No, inside container logic.
            # Actually, if I run this inside 'api' container, localhost:8000 works.
            
            response = requests.post(API_URL, json=payload, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("alert_status", "UNKNOWN")
                print(f"[{i+1}/{len(targets)}] {ward} | {organism[:15]}... | {antibiotic} -> {status}")
                success_count += 1
            else:
                print(f"[{i+1}/{len(targets)}] ❌ API Error {response.status_code}: {response.text}")
                error_count += 1
                
        except Exception as e:
            print(f"[{i+1}/{len(targets)}] ❌ Request Failed: {e}")
            error_count += 1
            
        # Small delay to prevent database lockups (simulating real-time processing)
        # time.sleep(0.05) 

    duration = time.time() - start_time
    print("="*60)
    print(f"🏁 SWEEP COMPLETE in {duration:.2f} seconds.")
    print(f"✅ Successful Predictions: {success_count}")
    print(f"❌ Failures: {error_count}")
    print("="*60)

if __name__ == "__main__":
    main()
