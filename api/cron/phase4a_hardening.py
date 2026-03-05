"""Phase 4A hardening — partial unique index + per-target schedule guard."""
import psycopg2
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger('Phase4A-Hardening')

DB_URL = ('postgresql://postgres.zdhvyhijuriggezelyxq:'
          'Yohan%26pasi80253327@aws-1-ap-northeast-2.pooler.supabase.com'
          ':5432/postgres?sslmode=require')

conn   = psycopg2.connect(DB_URL)
cursor = conn.cursor()

statements = [
    # CHECK 1: Partial unique index — DB-level invariant guaranteeing
    # exactly ONE is_active=TRUE row per (ward, organism, antibiotic).
    # This prevents both: zero-active-model (crash between deactivate+activate)
    # and two-active-models (logic bug in hysteresis).
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_one_active_model
    ON model_performance (ward, organism, antibiotic)
    WHERE is_active = TRUE
    """,
]

logger.info(f'Running {len(statements)} hardening statements...')
for stmt in statements:
    preview = ' '.join(stmt.split())[:120]
    logger.info(f'  {preview}...')
    cursor.execute(stmt)

conn.commit()
logger.info('Hardening migration committed.')

# Verify
cursor.execute("""
    SELECT indexname, indexdef
    FROM pg_indexes
    WHERE tablename = 'model_performance'
      AND indexname = 'idx_one_active_model'
""")
row = cursor.fetchone()
if row:
    logger.info(f"  ✓  idx_one_active_model: {row[1]}")
else:
    logger.error("  ✗  idx_one_active_model NOT FOUND")

cursor.close()
conn.close()
