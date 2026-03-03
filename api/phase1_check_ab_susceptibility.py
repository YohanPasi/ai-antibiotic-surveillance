from database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
print("Checking susceptibility_percent for AB targets...")
try:
    rows = db.execute(text("SELECT ward, antibiotic, total_tested, susceptibility_percent FROM ast_weekly_aggregated WHERE organism = 'Acinetobacter baumannii' AND total_tested >= 3 LIMIT 10")).fetchall()
    for r in rows:
        print(r)
except Exception as e:
    print(e)
db.close()
