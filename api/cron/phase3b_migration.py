"""Phase 3B migration — extends model_performance for rolling metrics."""
import psycopg2
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger('Phase3B-Migration')

DB_URL = ('postgresql://postgres.zdhvyhijuriggezelyxq:'
          'Yohan%26pasi80253327@aws-1-ap-northeast-2.pooler.supabase.com'
          ':5432/postgres?sslmode=require')

conn   = psycopg2.connect(DB_URL)
cursor = conn.cursor()

statements = [
    # Rolling metrics columns
    "ALTER TABLE model_performance ADD COLUMN IF NOT EXISTS validated_count INT DEFAULT 0",
    "ALTER TABLE model_performance ADD COLUMN IF NOT EXISTS mean_bias FLOAT",
    "ALTER TABLE model_performance ADD COLUMN IF NOT EXISTS mda FLOAT",
    "ALTER TABLE model_performance ADD COLUMN IF NOT EXISTS degradation_flagged BOOLEAN DEFAULT FALSE",
    "ALTER TABLE model_performance ADD COLUMN IF NOT EXISTS performance_status VARCHAR(30)",
    "ALTER TABLE model_performance ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW()",

    # Rolling time-window index for fast 12-week lookups in Phase 3B
    "CREATE INDEX IF NOT EXISTS idx_fvl_roll ON forecast_validation_log (ward, organism, antibiotic, forecast_week DESC)",
]

logger.info(f'Running {len(statements)} Phase 3B schema statements...')
for stmt in statements:
    logger.info(f'  {stmt[:90].replace(chr(10), " ")}...')
    cursor.execute(stmt)

conn.commit()
logger.info('Phase 3B migration committed.')

# ── Verify ────────────────────────────────────────────────────────────────────
cursor.execute(
    "SELECT column_name, is_nullable FROM information_schema.columns "
    "WHERE table_name='model_performance' ORDER BY ordinal_position"
)
cols = [(r[0], r[1]) for r in cursor.fetchall()]
logger.info('model_performance columns after migration:')
required = ['validated_count', 'mean_bias', 'mda', 'degradation_flagged', 'performance_status', 'updated_at']
all_ok = True
for col, nullable in cols:
    marker = '✓' if col in required else ' '
    logger.info(f'  {marker}  {col:40s}  nullable={nullable}')

for r in required:
    if r not in [c[0] for c in cols]:
        logger.error(f'  MISSING: {r}')
        all_ok = False

cursor.close()
conn.close()

if all_ok:
    logger.info('ALL PHASE 3B SCHEMA CHECKS PASSED.')
else:
    logger.error('SOME COLUMNS MISSING — check errors above.')
