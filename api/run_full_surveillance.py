import urllib.request
import json
import time
from sqlalchemy import create_engine, text
import os

# Database Config (Internal Docker Network)
# Using 'db' hostname as this runs inside the container network
DATABASE_URL = "postgresql://ast_user:ast_password_2024@db:5432/ast_db"
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
            # Prepare Request
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(API_URL, data=data, headers={
                'Content-Type': 'application/json',
                'User-Agent': 'SurveillanceSweep/1.0'
            })
            
            # Send Request
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    response_body = response.read().decode('utf-8')
                    data = json.loads(response_body)
                    status = data.get("alert_status", "UNKNOWN")
                    print(f"[{i+1}/{len(targets)}] {ward} | {organism[:15]}... | {antibiotic} -> {status}")
                    success_count += 1
                else:
                    print(f"[{i+1}/{len(targets)}] ❌ API Error {response.status}")
                    error_count += 1
                
        except Exception as e:
            print(f"[{i+1}/{len(targets)}] ❌ Request Failed: {e}")
            error_count += 1
            
        # Small delay to prevent overload? No, let's go fast.
    
    duration = time.time() - start_time
    print("="*60)
    print(f"🏁 SWEEP COMPLETE in {duration:.2f} seconds.")
    print(f"✅ Successful Predictions: {success_count}")
    print(f"❌ Failures: {error_count}")
    print("="*60)

if __name__ == "__main__":
    main()
