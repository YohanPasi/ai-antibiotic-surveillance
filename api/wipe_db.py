import os, psycopg2, logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
conn.autocommit = True
cur = conn.cursor()

tables = [
    'ast_raw_data',
    'ast_manual_entry',
    'ast_weekly_aggregated',
    'ast_baselines',
    'stp_model_registry',
    'stp_model_predictions',
    'stp_model_explanations',
    'stp_early_warnings',
    'stp_model_drift_metrics',
    'model_performance',
    'forecast_validation_log',
    'surveillance_logs',
    'predictions'
]

for table in tables:
    try:
        cur.execute(f'TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;')
        logger.info(f'Cascading truncate successful for {table}')
    except Exception as e:
        logger.warning(f'Could not truncate {table}: {e}')

conn.close()
