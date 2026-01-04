import os
import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
import json

DATABASE_URL = os.getenv("DATABASE_URL")

def seed_data():
    if not DATABASE_URL:
        print("Error: No DB URL")
        return

    print("🌱 Seeding Stage E Data...")
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # 1. Seed Assessments for Heatmap (Last 14 days)
        wards = ["ICU", "Surgical-A", "Gen-Med", "Pediatrics"]
        bands = ["RED", "AMBER", "GREEN"]
        
        print("   - Injecting Risk Assessments...")
        for _ in range(30):
            ward = random.choice(wards)
            band = random.choice(bands) if ward != "ICU" else "RED" # Bias ICU to RED
            
            conn.execute(text("""
                INSERT INTO mrsa_risk_assessments 
                (ward, sample_type, timestamp, risk_band, input_snapshot, consensus_band, confidence_level, consensus_version)
                VALUES (:ward, 'Blood', :ts, :band, '{}', :band, 'HIGH', 'v1.0')
            """), {
                "ward": ward,
                "ts": datetime.now() - timedelta(days=random.randint(0, 14)),
                "band": band
            })

        # 2. Seed Validation Logs for KPIS (Last 30 days)
        # We need realistic NPV/Sensitivity
        # NPV = TN / (TN + FN). High NPV means few False Negatives.
        # FN = Actual MRSA (True) but Pred != Red.
        
        print("   - Injecting Validation Logs...")
        # Scenario: Good model (NPV ~95%)
        # 50 Total: 
        #   - 20 True Negatives (Correct Green)
        #   - 20 True Positives (Correct Red)
        #   - 2 False Positives (Safe Error)
        #   - 1 False Negative (Danger Error)
        
        logs = []
        
        # True Negatives (Actual=False, Pred=Green)
        for _ in range(20):
            logs.append((False, "GREEN"))
            
        # True Positives (Actual=True, Pred=Red)
        for _ in range(20):
            logs.append((True, "RED"))
            
        # False Positives (Actual=False, Pred=Red) - Risk Aversion
        for _ in range(5):
            logs.append((False, "RED"))
            
        # False Negatives (Actual=True, Pred=Green) - The "Misses"
        for _ in range(2):
            logs.append((True, "GREEN"))

        for actual, pred in logs:
            conn.execute(text("""
                INSERT INTO mrsa_validation_log
                (validation_date, ward, sample_type, cefoxitin_result, actual_mrsa, 
                 consensus_band, rf_band, xgb_band, consensus_correct)
                VALUES (:date, 'ICU', 'Blood', :fox, :act, :con, :rf, :xgb, :correct)
            """), {
                "date": datetime.now() - timedelta(days=random.randint(0, 30)),
                "fox": "R" if actual else "S",
                "act": actual,
                "con": pred,
                "rf": pred, # Simplify: Models agree
                "xgb": pred,
                "correct": (actual == (pred == "RED"))
            })

        conn.commit()
        print("✅ Seeding Complete.")

if __name__ == "__main__":
    seed_data()
