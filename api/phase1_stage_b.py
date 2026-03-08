"""
Phase 1 - Stage B + Sweep runner.
Run this AFTER Stage A completes.
"""
from data_processor.aggregate_weekly import aggregate_weekly_data
from database import SessionLocal
from sqlalchemy import text
import logging
logging.basicConfig(level=logging.INFO)

# Stage B
print("=== Running Stage B ===")
ok = aggregate_weekly_data()
print(f"Stage B: {'OK' if ok else 'FAILED'}")

# Verify results
db = SessionLocal()
rows = db.execute(text(
    "SELECT organism, COUNT(*) cnt FROM ast_weekly_aggregated GROUP BY organism ORDER BY cnt DESC"
)).fetchall()
print("\nast_weekly_aggregated after Stage B:")
for r in rows:
    print(f"  {r[0]!r}: {r[1]} rows")

raw_rows = db.execute(text(
    "SELECT sub_organism, COUNT(*) cnt FROM ast_raw_data GROUP BY sub_organism ORDER BY cnt DESC"
)).fetchall()
print("\nast_raw_data after Stage A:")
for r in raw_rows:
    print(f"  {r[0]!r}: {r[1]} rows")
db.close()

print("\nDone. Now trigger /api/admin/sweep via the API to rebuild surveillance_logs.")
