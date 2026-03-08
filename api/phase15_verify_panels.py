from database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
print('--- DISTINCT AGGREGATED PANEL COMBINATIONS ---')
raw = db.execute(text("SELECT DISTINCT organism, antibiotic FROM ast_weekly_aggregated ORDER BY organism, antibiotic")).fetchall()
for r in raw: print(f'{r[0]} | {r[1]}')

print('\n--- SURVEILLANCE LOGS COUNTS BY ORGANISM ---')
counts = db.execute(text("SELECT organism, COUNT(*) FROM surveillance_logs GROUP BY organism")).fetchall()
for c in counts: print(f'{c[0]}: {c[1]}')
db.close()
