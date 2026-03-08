from database import SessionLocal
from sqlalchemy import text
from ai_models.prediction_engine import SurveillancePredictor
import logging

logging.basicConfig(level=logging.INFO)
db = SessionLocal()

ward = '05'
org = 'Acinetobacter baumannii'
abx = 'Cefepime(FEP)'

print(f"Testing sweep logic for {ward}, {org}, {abx}")

rows = db.execute(text("""
    SELECT susceptibility_percent, susceptible_count, total_tested, week_start_date
    FROM ast_weekly_aggregated
    WHERE organism = :organism AND antibiotic = :antibiotic
      AND ward = :ward AND total_tested >= 3
    ORDER BY week_start_date DESC LIMIT 5
"""), {"organism": org, "antibiotic": abx, "ward": ward}).fetchall()

print("Rows fetched:", rows)

history_data = [float(r[0]) for r in rows if r[0] is not None]
print("History Data:", history_data)

if not history_data:
    print("Would SKIP due to no history data.")
else:
    predictor = SurveillancePredictor()
    pred = predictor.predict(history_data, ward, org, abx)
    print("Prediction:", pred)

db.close()
