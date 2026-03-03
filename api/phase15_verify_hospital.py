from database import SessionLocal
from sqlalchemy import text
db = SessionLocal()

print('--- HOSPITAL-WIDE AGGREGATION CHECK ---')
try:
    res = db.execute(text("SELECT DISTINCT organism, antibiotic FROM organism_level_aggregation WHERE organism IN ('Pseudomonas aeruginosa', 'Acinetobacter baumannii')")).fetchall()
    for r in res: print(f"{r[0]} | {r[1]}")
except Exception as e:
    print('Failed:', e)
finally:
    db.close()
