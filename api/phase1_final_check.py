from database import SessionLocal
from sqlalchemy import text
db = SessionLocal()

print("--- Raw Data ---")
raw = db.execute(text("SELECT sub_organism as organism, COUNT(*) FROM ast_raw_data GROUP BY sub_organism")).fetchall()
for r in raw: print(f"{r[0]}: {r[1]}")

print("\n--- Aggregated ---")
agg = db.execute(text("SELECT organism, COUNT(*) FROM ast_weekly_aggregated GROUP BY organism")).fetchall()
for r in agg: print(f"{r[0]}: {r[1]}")

print("\n--- Surveillance Logs ---")
surv = db.execute(text("SELECT organism, COUNT(*) FROM surveillance_logs GROUP BY organism")).fetchall()
for r in surv: print(f"{r[0]}: {r[1]}")

db.close()
