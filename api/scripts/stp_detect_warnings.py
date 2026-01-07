
import sys
import os
import uuid
from sqlalchemy import text

# Add /app to python path for Docker compatibility
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, engine

def unique_uuid():
    return str(uuid.uuid4())

def detect_warnings():
    print("Connecting to database...")
    db = SessionLocal()
    
    try:
        print("Detecting warnings from significant trends (Slope > 5%)...")
        
        # 1. Fetch Trends
        trends = db.execute(text("""
            SELECT ward, organism, antibiotic, week_start, rolling_slope 
            FROM stp_temporal_trend_signals 
            WHERE ABS(rolling_slope) > 0.05
        """)).fetchall()
        
        # 2. Prepare Data
        new_warnings = []
        for t in trends:
            severity = 'HIGH' if t.rolling_slope > 0.1 else 'MEDIUM'
            # Naive de-duplication: One warning per ward-bug-drug (latest)
            # But let's just insert all significant weeks for now, or use ON CONFLICT if constraint exists.
            # Schema has no unique constraint on (ward, organism, antibiotic, week). 
            # I will uniqueify in python:
            new_warnings.append({
                "warning_id": str(uuid.uuid4()),
                "ward": t.ward,
                "organism": t.organism,
                "antibiotic": t.antibiotic,
                "detected_at_week": str(t.week_start),
                "signal_strength": t.rolling_slope,
                "method": "TrendSlope",
                "severity": severity,
                "status": "new"
            })
            
        if not new_warnings:
            print("No significant trends found.")
            return

        # 3. Bulk Insert (Raw SQL)
        print(f"Inserting {len(new_warnings)} warnings...")
        
        if not new_warnings:
            print("No significant trends found.")
            return

        # 3. Insert Row-by-Row
        print(f"Inserting {len(new_warnings)} warnings (row-by-row)...")
        
        insert_query = text("""
            INSERT INTO stp_early_warnings (
                warning_id, ward, organism, antibiotic, detected_at_week, 
                signal_strength, method, severity, status
            ) VALUES (:warning_id, :ward, :organism, :antibiotic, :detected_at_week, 
                      :signal_strength, :method, :severity, :status)
        """)
        
        count = 0
        for w in new_warnings:
             params = {
                "warning_id": str(w["warning_id"]),
                "ward": str(w["ward"]),
                "organism": str(w["organism"]),
                "antibiotic": str(w["antibiotic"]),
                "detected_at_week": str(w["detected_at_week"]),
                "signal_strength": float(w["signal_strength"]),
                "method": str(w["method"]),
                "severity": str(w["severity"]),
                "status": "new"
            }
             try:
                db.execute(insert_query, params)
                db.commit() # Commit each row to isolate failures
                count += 1
             except Exception as e:
                db.rollback() # Rollback only this transaction attempt
                print(f"Skipping row: {e}")
        
        db.commit()
        print(f"✅ Detection complete. Inserted {count} REAL warnings based on trends.")
        
    except Exception as e:
        print(f"Error during detection: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    detect_warnings()
