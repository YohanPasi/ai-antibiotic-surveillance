#!/usr/bin/env python3
"""Quick diagnostic of validation pipeline"""
import sys
sys.path.append('/app')

from database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

print("=== VALIDATION PIPELINE DIAGNOSTIC ===\n")

# 1. Check raw submissions
raw_count = db.execute(text("SELECT COUNT(*) FROM stp_external_ast_raw")).scalar()
print(f"1. Raw AST Submissions: {raw_count}")

if raw_count > 0:
    recent = db.execute(text("""
        SELECT ward, organism, COUNT(*) as count
        FROM stp_external_ast_raw
        GROUP BY ward, organism
        LIMIT 3
    """)).fetchall()
    for r in recent:
        print(f"   - {r.ward} / {r.organism}: {r.count} results")

# 2. Check derived rates
derived_count = db.execute(text("SELECT COUNT(*) FROM stp_external_resistance_derived")).scalar()
print(f"\n2. Derived Resistance Rates: {derived_count}")

# 3. Check predictions
pred_count = db.execute(text("SELECT COUNT(*) FROM stp_model_predictions")).scalar()
print(f"\n3. Model Predictions Available: {pred_count}")

if pred_count > 0:
    preds = db.execute(text("""
        SELECT DISTINCT ward, organism
        FROM stp_model_predictions
        LIMIT 3
    """)).fetchall()
    for p in preds:
        print(f"   - {p.ward} / {p.organism}")

# 4. Check validations
val_count = db.execute(text("SELECT COUNT(*) FROM stp_prediction_validation_events")).scalar()
print(f"\n4. Validation Events: {val_count}")

print("\n=== DIAGNOSIS ===")
if raw_count == 0:
    print("❌ No AST data submitted yet")
elif derived_count == 0:
    print("❌ AST submitted but derivation FAILED")
    print("   → Check derivation logic")
elif pred_count == 0:
    print("⚠️  AST & derivation OK, but NO PREDICTIONS exist")
    print("   → You need to run Stage 3 predictions first")
elif val_count == 0:
    print("⚠️  Everything exists but NO MATCH between submissions & predictions")
    print("   → Check if ward/organism/week alignsalign")
else:
    print("✅ Pipeline working!")

db.close()
