"""Run Phase 3A migration v2 and verify all schema requirements."""
import psycopg2
import logging
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger('Phase3A-Migration')

DB_URL = ('postgresql://postgres.zdhvyhijuriggezelyxq:'
          'Yohan%26pasi80253327@aws-1-ap-northeast-2.pooler.supabase.com'
          ':5432/postgres?sslmode=require')

conn   = psycopg2.connect(DB_URL)
cursor = conn.cursor()

# Run each ALTER / CREATE statement explicitly — no SQL file parsing
statements = [
    # predictions — new audit columns
    "ALTER TABLE predictions ADD COLUMN IF NOT EXISTS direction_correct BOOLEAN",
    "ALTER TABLE predictions ADD COLUMN IF NOT EXISTS revision_flag BOOLEAN DEFAULT FALSE",
    "ALTER TABLE predictions ADD COLUMN IF NOT EXISTS validated_at TIMESTAMP",

    # forecast_validation_log — proper audit trail table
    """CREATE TABLE IF NOT EXISTS forecast_validation_log (
        id                  SERIAL PRIMARY KEY,
        ward                VARCHAR(100) NOT NULL,
        organism            VARCHAR(200) NOT NULL,
        antibiotic          VARCHAR(200) NOT NULL,
        forecast_week       DATE         NOT NULL,
        predicted_s_percent FLOAT        NOT NULL,
        actual_s_percent    FLOAT        NOT NULL,
        prediction_error    FLOAT        NOT NULL,
        direction_correct   BOOLEAN,
        revision_flag       BOOLEAN      DEFAULT FALSE,
        validated_at        TIMESTAMP    DEFAULT NOW(),
        model_version       VARCHAR(100)
    )""",

    # Unique index — one validation row per (ward, org, abx, week)
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_fvl_unique ON forecast_validation_log (ward, organism, antibiotic, forecast_week)",
    # Target index — fast rolling MAE lookups (Phase 3B)
    "CREATE INDEX IF NOT EXISTS idx_fvl_target ON forecast_validation_log (ward, organism, antibiotic)",
    # Week index — rolling window queries (G1 + G6)
    "CREATE INDEX IF NOT EXISTS idx_fvl_week ON forecast_validation_log (forecast_week)",
]

logger.info(f'Running {len(statements)} schema statements...')
for stmt in statements:
    preview = stmt[:80].replace('\n', ' ')
    logger.info(f'  {preview}...')
    cursor.execute(stmt)

conn.commit()
logger.info('Migration committed successfully.')

# ── Verification ──────────────────────────────────────────────────────────────

# 1. predictions columns
cursor.execute(
    "SELECT column_name FROM information_schema.columns WHERE table_name='predictions' ORDER BY ordinal_position"
)
pred_cols = [r[0] for r in cursor.fetchall()]
all_ok = True
for col in ['direction_correct', 'revision_flag', 'validated_at']:
    ok = col in pred_cols
    logger.info(f'  predictions.{col}: {"OK" if ok else "MISSING"}')
    if not ok:
        all_ok = False

# 2. forecast_validation_log columns
cursor.execute(
    "SELECT column_name FROM information_schema.columns WHERE table_name='forecast_validation_log' ORDER BY ordinal_position"
)
fvl_cols = [r[0] for r in cursor.fetchall()]
logger.info(f'forecast_validation_log columns: {fvl_cols}')
for col in ['ward', 'organism', 'antibiotic', 'forecast_week',
            'predicted_s_percent', 'actual_s_percent', 'prediction_error',
            'direction_correct', 'revision_flag', 'validated_at']:
    ok = col in fvl_cols
    logger.info(f'  fvl.{col}: {"OK" if ok else "MISSING"}')
    if not ok:
        all_ok = False

# 3. Indexes
for idx in ['idx_fvl_unique', 'idx_fvl_target', 'idx_fvl_week']:
    cursor.execute("SELECT indexname FROM pg_indexes WHERE indexname=%s", (idx,))
    exists = cursor.fetchone() is not None
    logger.info(f'  Index {idx}: {"EXISTS" if exists else "MISSING"}')
    if not exists:
        all_ok = False

# 4. Epi-time anchor
cursor.execute('SELECT MAX(week_start_date) FROM ast_weekly_aggregated')
logger.info(f'  last_data_week (R1 anchor): {cursor.fetchone()[0]}')

# 5. Predictions row count
cursor.execute('SELECT COUNT(*) FROM predictions')
logger.info(f'  predictions rows: {cursor.fetchone()[0]}')

cursor.close()
conn.close()

if all_ok:
    logger.info('ALL CHECKS PASSED — Phase 3A schema ready.')
else:
    logger.error('SOME CHECKS FAILED.')
