"""Phase 4A migration — adds active model tracking and backtest schedule columns."""
import psycopg2
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger('Phase4A-Migration')

DB_URL = ('postgresql://postgres.zdhvyhijuriggezelyxq:'
          'Yohan%26pasi80253327@aws-1-ap-northeast-2.pooler.supabase.com'
          ':5432/postgres?sslmode=require')

conn   = psycopg2.connect(DB_URL)
cursor = conn.cursor()

statements = [
    # is_active tracks which model is currently selected per target
    # (distinct from is_best_model which was the original ML training column)
    "ALTER TABLE model_performance ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT FALSE",

    # Weekly backtest schedule guard
    "ALTER TABLE model_performance ADD COLUMN IF NOT EXISTS last_backtest_at TIMESTAMP",

    # Log every model switch event for publication-grade audit trail
    """
    CREATE TABLE IF NOT EXISTS model_switch_log (
        id              SERIAL PRIMARY KEY,
        ward            VARCHAR(100),
        organism        VARCHAR(200) NOT NULL,
        antibiotic      VARCHAR(200) NOT NULL,
        switched_at     TIMESTAMP DEFAULT NOW(),
        old_model       VARCHAR(50),
        new_model       VARCHAR(50) NOT NULL,
        old_mae         FLOAT,
        new_mae         FLOAT,
        delta_mae       FLOAT,
        reason          VARCHAR(50) DEFAULT 'HYSTERESIS_PASSED',
        epi_week        DATE
    )
    """,

    # Index for audit lookups
    "CREATE INDEX IF NOT EXISTS idx_msl_target ON model_switch_log (ward, organism, antibiotic, switched_at DESC)",
]

logger.info(f'Running {len(statements)} Phase 4A schema statements...')
for stmt in statements:
    preview = ' '.join(stmt.split())[:100]
    logger.info(f'  {preview}...')
    cursor.execute(stmt)

conn.commit()
logger.info('Phase 4A migration committed.')

# Verify
cursor.execute(
    "SELECT column_name FROM information_schema.columns "
    "WHERE table_name='model_performance' ORDER BY ordinal_position"
)
all_cols = [r[0] for r in cursor.fetchall()]
required = ['is_active', 'last_backtest_at']
for col in required:
    status = '✓' if col in all_cols else '✗ MISSING'
    logger.info(f"  {status}  model_performance.{col}")

cursor.execute("SELECT to_regclass('public.model_switch_log')")
exists = cursor.fetchone()[0]
logger.info(f"  {'✓' if exists else '✗ MISSING'}  model_switch_log table")

cursor.close()
conn.close()
