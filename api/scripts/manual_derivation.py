#!/usr/bin/env python3
"""Manually trigger derivation for existing submissions"""
import sys
sys.path.append('/app')

from database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

print("=== MANUAL DERIVATION TRIGGER ===\n")

# Get submissions
submissions = db.execute(text("""
    SELECT DISTINCT ward, organism, sample_date
    FROM stp_external_ast_raw
    ORDER BY sample_date DESC
    LIMIT 5
""")).fetchall()

print(f"Found {len(submissions)} submission groups\n")

for sub in submissions:
    print(f"Processing: {sub.ward} / {sub.organism} / {sub.sample_date}")
    
    # Manual derivation
    week_start = db.execute(text("""
        SELECT DATE_TRUNC('week', :date::date) as week
    """), {"date": sub.sample_date}).scalar()
    
    # Simplified aggregation (no completeness for now)
    try:
        db.execute(text("""
            INSERT INTO stp_external_resistance_derived (
                ward, organism, antibiotic, week_start,
                s_count, i_count, r_count, na_count, tested_count,
                resistance_rate, is_stable,
                completeness_ratio, expected_antibiotics, tested_antibiotics
            )
            SELECT 
                ward, organism, antibiotic, :week_start,
                SUM(CASE WHEN ast_result = 'S' THEN 1 ELSE 0 END),
                SUM(CASE WHEN ast_result = 'I' THEN 1 ELSE 0 END),
                SUM(CASE WHEN ast_result = 'R' THEN 1 ELSE 0 END),
                SUM(CASE WHEN ast_result = 'NA' THEN 1 ELSE 0 END),
                SUM(CASE WHEN ast_result IN ('S','I','R') THEN 1 ELSE 0 END) as tested,
                CASE 
                    WHEN SUM(CASE WHEN ast_result IN ('S','I','R') THEN 1 ELSE 0 END) = 0 THEN NULL
                    ELSE SUM(CASE WHEN ast_result = 'R' THEN 1 ELSE 0 END)::float / 
                         SUM(CASE WHEN ast_result IN ('S','I','R') THEN 1 ELSE 0 END)
                END,
                SUM(CASE WHEN ast_result IN ('S','I','R') THEN 1 ELSE 0 END) >= 10,
                1.0, 10, 10
            FROM stp_external_ast_raw
            WHERE ward = :ward
              AND organism = :organism
              AND DATE_TRUNC('week', sample_date) = :week_start
            GROUP BY ward, organism, antibiotic
            ON CONFLICT (ward, organism, antibiotic, week_start) DO NOTHING
        """), {
            "ward": sub.ward,
            "organism": sub.organism,
            "week_start": week_start
        })
        db.commit()
        print(f"  ✅ Derived")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        db.rollback()

print("\n=== CHECKING RESULTS ===")
derived_count = db.execute(text("SELECT COUNT(*) FROM stp_external_resistance_derived")).scalar()
print(f"Total derived records: {derived_count}")

db.close()
