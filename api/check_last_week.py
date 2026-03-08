from database import SessionLocal
from sqlalchemy import text
from datetime import timedelta
db = SessionLocal()
row = db.execute(text("SELECT MAX(week_start_date) FROM ast_weekly_aggregated WHERE organism IN ('Pseudomonas aeruginosa', 'Acinetobacter baumannii') AND total_tested >= 3")).fetchone()
last = row[0]
predicted = last + timedelta(days=7) if last else None
print(f"last_data_week      : {last}")
print(f"predicted_week_start: {predicted}")
db.close()
