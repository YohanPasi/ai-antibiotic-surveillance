from database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
print('--- Antibiotics ---')
raw = db.execute(text("SELECT DISTINCT antibiotic FROM ast_weekly_aggregated ORDER BY antibiotic")).fetchall()
for r in raw: print(r[0])
db.close()
