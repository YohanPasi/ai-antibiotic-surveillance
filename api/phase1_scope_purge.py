"""
Phase 1 Scope Purge Script
- Remove non-NF organisms from surveillance_logs and ast_weekly_aggregated
- Rename 'Acinetobacter spp.' entries to canonical 'Acinetobacter baumannii'
- Trigger a fresh surveillance sweep
- Print final DB state for verification
"""
from database import SessionLocal
from sqlalchemy import text
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("phase1_purge")

db = SessionLocal()
try:
    NF_TUPLE = "('Pseudomonas aeruginosa', 'Acinetobacter baumannii')"

    # 1. Rename Acinetobacter spp. rows to canonical name (before we purge)
    r3 = db.execute(text(
        "UPDATE ast_weekly_aggregated SET organism = 'Acinetobacter baumannii' "
        "WHERE organism ILIKE 'Acinetobacter spp%'"
    ))
    logger.info(f"RENAME  ast_weekly_aggregated: {r3.rowcount} Acinetobacter spp rows -> baumannii")

    # Also rename in surveillance_logs if any
    r4 = db.execute(text(
        "UPDATE surveillance_logs SET organism = 'Acinetobacter baumannii' "
        "WHERE organism ILIKE 'Acinetobacter spp%'"
    ))
    logger.info(f"RENAME  surveillance_logs: {r4.rowcount} Acinetobacter spp rows -> baumannii")

    # 2. Purge non-NF from surveillance_logs
    r1 = db.execute(text(
        f"DELETE FROM surveillance_logs WHERE organism NOT IN {NF_TUPLE}"
    ))
    logger.info(f"PURGE   surveillance_logs: {r1.rowcount} non-NF rows deleted")

    # 3. Purge non-NF from ast_weekly_aggregated
    r2 = db.execute(text(
        f"DELETE FROM ast_weekly_aggregated WHERE organism NOT IN {NF_TUPLE}"
    ))
    logger.info(f"PURGE   ast_weekly_aggregated: {r2.rowcount} non-NF rows deleted")

    db.commit()
    logger.info("Commit successful.")

    # 4. Verify final state
    print("\n=== VERIFICATION ===")
    for table in ("ast_raw_data", "ast_weekly_aggregated", "surveillance_logs"):
        src_col = "sub_organism" if table == "ast_raw_data" else "organism"
        rows = db.execute(text(
            f"SELECT {src_col}, COUNT(*) cnt FROM {table} GROUP BY {src_col} ORDER BY cnt DESC"
        )).fetchall()
        print(f"\n{table} ({src_col}):")
        for r in rows:
            print(f"  {r[0]!r}: {r[1]}")

except Exception as e:
    db.rollback()
    logger.error(f"Error: {e}")
    raise
finally:
    db.close()
    print("\nDone.")
