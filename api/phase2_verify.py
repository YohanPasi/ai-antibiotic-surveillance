"""
Phase 2 Direct Verification Script
Tests: culture_date ISO week bucketing (no HTTP call needed)
"""
from database import SessionLocal
from sqlalchemy import text
from datetime import datetime, timedelta
import subprocess

db = SessionLocal()
backdated = (datetime.now() - timedelta(days=10)).date()
print(f"Testing Phase 2 with culture_date = {backdated}")

# 1. Insert directly into ast_manual_entry with backdated culture_date
print("\n--- Step 1: Direct DB Insert ---")
try:
    db.execute(text("""
        INSERT INTO ast_manual_entry (culture_date, lab_no, age, gender, bht, ward, specimen_type, organism, antibiotic, result)
        VALUES (:cd, :lab, :age, :gen, :bht, :ward, :spec, :org, :abx, :res)
    """), {
        "cd": backdated,
        "lab": f"TEST-PHASE2-{backdated}",
        "age": 45, "gen": "Male", "bht": "BHT-PH2",
        "ward": "ICU", "spec": "Blood",
        "org": "Pseudomonas aeruginosa",
        "abx": "Meropenem  (MEM)", "res": "R"
    })
    db.commit()
    print("Insert committed successfully.")
except Exception as e:
    db.rollback()
    print(f"Insert failed: {e}")

# 2. Confirm the entry is stored with correct dates
print("\n--- Step 2: Verify DB Entry ---")
row = db.execute(text("""
    SELECT culture_date, created_at 
    FROM ast_manual_entry 
    WHERE lab_no = :lab 
    LIMIT 1
"""), {"lab": f"TEST-PHASE2-{backdated}"}).fetchone()

if row:
    c_date, sys_date = row
    print(f"culture_date  : {c_date}  (should be {backdated})")
    print(f"created_at    : {sys_date}  (should be today)")
    if str(c_date) == str(backdated):
        print("✅ PASS: culture_date correctly stored as past date")
    else:
        print("❌ FAIL: culture_date does not match")
    if c_date != sys_date.date():
        print("✅ PASS: culture_date ≠ created_at (separation confirmed)")
    else:
        print("⚠ culture_date and created_at are the same day (may be coincidence if today − 10d is the same weekday as creation)")
else:
    print("❌ FAIL: No row found.")

db.close()

# 3. Run Stage B to rebuild aggregation
print("\n--- Step 3: Running Stage B Aggregation ---")
result = subprocess.run(["python", "/app/data_processor/aggregate_weekly.py"], capture_output=True, text=True)
print(result.stdout[-500:] if result.stdout else "No stdout")
if result.returncode != 0:
    print("Stage B Error:", result.stderr[-300:])

# 4. Verify bucketing in ast_weekly_aggregated
print("\n--- Step 4: Verify ISo Week Bucketing ---")
from datetime import date
week_start = backdated - timedelta(days=backdated.weekday())
print(f"Expected ISO week_start_date: {week_start}")

db = SessionLocal()
rows = db.execute(text("""
    SELECT week_start_date, total_tested, susceptible_count, resistant_count
    FROM ast_weekly_aggregated
    WHERE ward = 'ICU' AND organism = 'Pseudomonas aeruginosa' AND antibiotic = 'Meropenem  (MEM)'
    ORDER BY week_start_date DESC
    LIMIT 6
""")).fetchall()

print("Recent ICU / Pseudomonas / Meropenem aggregations:")
for r in rows:
    flag = "  <-- BACKDATED WEEK SHOULD APPEAR" if str(r[0]) == str(week_start) else ""
    print(f"  {r}{flag}")

db.close()

# 5. Cleanup the test row
print("\n--- Step 5: Cleanup test row ---")
db = SessionLocal()
db.execute(text("DELETE FROM ast_manual_entry WHERE lab_no = :lab"), {"lab": f"TEST-PHASE2-{backdated}"})
db.commit()
db.close()
print("Test row removed.")
print("\n✅ Phase 2 Verification Complete.")
