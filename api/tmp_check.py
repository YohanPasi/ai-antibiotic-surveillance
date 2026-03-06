import os, psycopg2
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

cur.execute('SELECT COUNT(*) FROM forecast_validation_log;')
print('Validation Log rows:', cur.fetchone()[0])

cur.execute('SELECT COUNT(*), MIN(target_week_start), MAX(target_week_start) FROM predictions;')
r = cur.fetchone()
print(f'Predictions: {r[0]} rows | Earliest: {r[1]} | Latest: {r[2]}')

cur.execute('SELECT MAX(week_start_date) FROM ast_weekly_aggregated;')
print('Last data week:', cur.fetchone()[0])

conn.close()
