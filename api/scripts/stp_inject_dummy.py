
import sys
import os
import uuid
from sqlalchemy import text

# Add /app to python path for Docker compatibility
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, engine

def inject_dummies():
    print("Connecting to database...")
    db = SessionLocal()
    
    try:
        print("Clearing StpEarlyWarnings...")
        db.execute(text("DELETE FROM stp_early_warnings"))
        db.commit()
        
        print("Injecting valid dummies...")
        
        dummies = [
            {
                "id": str(uuid.uuid4()),
                "ward": "ICU",
                "org": "E. coli",
                "abx": "Meropenem",
                "date": "2026-01-01",
                "sig": 0.85, # High Probability
                "method": "TrendSlope",
                "sev": "high"
            },
            {
                "id": str(uuid.uuid4()),
                "ward": "General Ward A",
                "org": "K. pneumoniae",
                "abx": "Ciprofloxacin",
                "date": "2026-01-02",
                "sig": 0.62, # Medium
                "method": "LSTM_v2",
                "sev": "medium"
            },
            {
                "id": str(uuid.uuid4()),
                "ward": "Surgical Ward",
                "org": "P. aeruginosa",
                "abx": "Gentamicin",
                "date": "2026-01-03",
                "sig": 0.91, # Very High
                "method": "TrendSlope",
                "sev": "high"
            }
        ]
        
        query = text("""
            INSERT INTO stp_early_warnings (
                warning_id, ward, organism, antibiotic, detected_at_week, 
                signal_strength, method, severity, status
            ) VALUES (:id, :ward, :org, :abx, :date, :sig, :method, :sev, 'new')
        """)
        
        for d in dummies:
            db.execute(query, d)
            
        db.commit()
        print(f"✅ Injected {len(dummies)} dummy warnings.")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    inject_dummies()
