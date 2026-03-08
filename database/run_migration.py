"""
Stage 4 — Run SQL migration using SQLAlchemy with proper statement handling.
Mounted at /app/database_scripts/run_migration.py inside the api container.

Run via: docker exec ast_api python /app/database_scripts/run_migration.py
"""
from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

statements = [
    # Add all 4 new columns individually (avoid comma-separated ALTER TABLE issues)
    "ALTER TABLE mrsa_raw_clean ADD COLUMN IF NOT EXISTS gram_stain VARCHAR(50)",
    "ALTER TABLE mrsa_raw_clean ADD COLUMN IF NOT EXISTS cell_count_category VARCHAR(10)",
    "ALTER TABLE mrsa_raw_clean ADD COLUMN IF NOT EXISTS recent_antibiotic_use VARCHAR(10) DEFAULT 'Unknown'",
    "ALTER TABLE mrsa_raw_clean ADD COLUMN IF NOT EXISTS length_of_stay INTEGER DEFAULT 0",

    # Backfill gram_stain from gram_positivity
    "UPDATE mrsa_raw_clean SET gram_stain = 'GPC' WHERE gram_positivity = 'GPC' AND gram_stain IS NULL",
    "UPDATE mrsa_raw_clean SET gram_stain = 'Unknown' WHERE gram_stain IS NULL",

    # Backfill cell_count_category from old ordinal integer (if column has numeric values)
    """
    UPDATE mrsa_raw_clean
    SET cell_count_category = CASE
        WHEN cell_count <= 1 THEN 'LOW'
        WHEN cell_count <= 3 THEN 'MEDIUM'
        ELSE 'HIGH'
    END
    WHERE cell_count_category IS NULL
      AND cell_count IS NOT NULL
    """,

    # Default any remaining nulls
    "UPDATE mrsa_raw_clean SET cell_count_category = 'LOW' WHERE cell_count_category IS NULL",
]

with engine.connect() as conn:
    for stmt in statements:
        stmt = stmt.strip()
        if not stmt:
            continue
        try:
            conn.execute(text(stmt))
            print(f"✅ OK: {stmt[:80].replace(chr(10),' ')}...")
        except Exception as e:
            print(f"⚠️  WARN ({stmt[:60].replace(chr(10),' ')}...): {e}")
    conn.commit()

print("\n=== Final column check ===")
with engine.connect() as conn:
    rows = conn.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'mrsa_raw_clean' ORDER BY ordinal_position"
    )).fetchall()
    cols = [r[0] for r in rows]
    print("Columns:", cols)

required = {'gram_stain', 'cell_count_category', 'recent_antibiotic_use', 'length_of_stay'}
missing = required - set(cols)
if missing:
    print(f"\n❌ Still missing: {missing}")
else:
    print("\n✅ Migration complete — all v2 columns present.")
