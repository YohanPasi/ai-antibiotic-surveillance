import os, psycopg2
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

# Check LSTM model registry details
cur.execute("""
    SELECT model_type, target, status, deployment_mode, metrics_json, created_at
    FROM stp_model_registry
    ORDER BY created_at DESC;
""")
registry = cur.fetchall()
print('=== STP MODEL REGISTRY ===')
for r in registry:
    print(f'Type: {r[0]} | Target: {r[1]} | Status: {r[2]} | Mode: {r[3]} | Created: {r[5]}')
    print(f'  Metrics: {r[4]}')

# Check predictions table for forecasts
cur.execute("SELECT model_used, COUNT(*) FROM predictions GROUP BY model_used;")
preds = cur.fetchall()
print('\n=== PREDICTIONS TABLE (by model) ===')
for p in preds:
    print(f'  {p[0]}: {p[1]} forecasts')

# Check forecast_validation_log
cur.execute("SELECT COUNT(*) FROM forecast_validation_log;")
print('\n=== FORECAST VALIDATION LOG ===')
print(f'  Total validations: {cur.fetchone()[0]}')

conn.close()
