from database import SessionLocal
from sqlalchemy import text
db = SessionLocal()

print('--- DEBUG AB TARGETS ---')
try:
    rows = db.execute(text("SELECT ward, organism, antibiotic, total_tested FROM ast_weekly_aggregated WHERE organism = 'Acinetobacter baumannii' AND total_tested >= 3 LIMIT 20")).fetchall()
    print(f"Sample targets for AB (>=3 tested): {len(rows)}")
    for r in rows:
        print(r)
except Exception as e:
    print(e)
db.close()
