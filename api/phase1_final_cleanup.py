"""
Phase 1 - Final cleanup: fix manual_entry contamination and trigger sweep.
"""
from database import SessionLocal
from sqlalchemy import text
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("phase1_final")

db = SessionLocal()
try:
    NF_TUPLE = "('Pseudomonas aeruginosa', 'Acinetobacter baumannii')"

    # 1. Fix ast_manual_entry: rename Acinetobacter spp -> baumannii
    r1 = db.execute(text(
        "UPDATE ast_manual_entry SET organism = 'Acinetobacter baumannii' "
        "WHERE organism ILIKE 'Acinetobacter spp%'"
    ))
    logger.info(f"RENAME  ast_manual_entry: {r1.rowcount} Acinetobacter spp rows -> baumannii")

    # 2. Purge non-NF from ast_manual_entry
    r2 = db.execute(text(
        f"DELETE FROM ast_manual_entry WHERE organism NOT IN {NF_TUPLE}"
    ))
    logger.info(f"PURGE   ast_manual_entry: {r2.rowcount} non-NF rows deleted")

    # 3. Purge from ast_weekly_aggregated (manual entry residuals)
    r3 = db.execute(text(
        f"DELETE FROM ast_weekly_aggregated WHERE organism NOT IN {NF_TUPLE}"
    ))
    logger.info(f"PURGE   ast_weekly_aggregated: {r3.rowcount} non-NF rows deleted")

    # 4. Rename Acinetobacter spp in ast_weekly_aggregated (if any survived)
    r4 = db.execute(text(
        "UPDATE ast_weekly_aggregated SET organism = 'Acinetobacter baumannii' "
        "WHERE organism ILIKE 'Acinetobacter spp%'"
    ))
    logger.info(f"RENAME  ast_weekly_aggregated: {r4.rowcount} Acinetobacter spp rows -> baumannii")

    db.commit()
    logger.info("Commit successful.")

    # 5. Final verification
    print("\n=== FINAL VERIFICATION ===")
    for table in ("ast_raw_data", "ast_weekly_aggregated", "ast_manual_entry"):
        src_col = "sub_organism" if table == "ast_raw_data" else "organism"
        rows = db.execute(text(
            f"SELECT {src_col}, COUNT(*) cnt FROM {table} GROUP BY {src_col} ORDER BY cnt DESC"
        )).fetchall()
        print(f"\n{table}:")
        for r in rows:
            print(f"  {r[0]!r}: {r[1]:,} rows")

    # 6. High-confidence signal count
    hc = db.execute(text(
        "SELECT organism, COUNT(*) cnt FROM ast_weekly_aggregated "
        "WHERE total_tested >= 3 GROUP BY organism ORDER BY cnt DESC"
    )).fetchall()
    print("\nHigh-confidence signals (total_tested >= 3):")
    for r in hc:
        print(f"  {r[0]!r}: {r[1]:,} rows")

except Exception as e:
    db.rollback()
    logger.error(f"Error: {e}")
    raise
finally:
    db.close()
    print("\nDone. Now triggering admin sweep via API...")
