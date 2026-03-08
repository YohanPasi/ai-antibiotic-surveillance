"""
Stage 4 helper — verifies mrsa_raw_clean columns exist after migration.
Run via: docker exec ast_api python /app/database_scripts/verify_columns.py
"""
from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    rows = conn.execute(text(
        "SELECT column_name, data_type "
        "FROM information_schema.columns "
        "WHERE table_name = 'mrsa_raw_clean' "
        "ORDER BY ordinal_position"
    )).fetchall()

print("=== mrsa_raw_clean columns ===")
for col_name, data_type in rows:
    marker = " ✓" if col_name in [
        'ward', 'sample_type', 'gram_stain', 'cell_count_category',
        'growth_time', 'recent_antibiotic_use', 'length_of_stay', 'mrsa_label'
    ] else ""
    print(f"  {col_name}: {data_type}{marker}")

required = {'ward', 'sample_type', 'gram_stain', 'cell_count_category',
            'growth_time', 'recent_antibiotic_use', 'length_of_stay', 'mrsa_label'}
present = {r[0] for r in rows}
missing = required - present

if missing:
    print(f"\n❌ MISSING COLUMNS: {missing}")
else:
    print("\n✅ All v2 feature columns present. Safe to proceed with ingest.")
