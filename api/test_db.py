import os, psycopg2, logging

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

cur.execute('SELECT COUNT(*) FROM ast_weekly_aggregated;')
print('Aggregated Rows:', cur.fetchone()[0])

cur.execute('SELECT COUNT(*) FROM stp_model_registry;')
print('Models Trained:', cur.fetchone()[0])

cur.execute('SELECT COUNT(*) FROM predictions;')
print('Forecasts Generated:', cur.fetchone()[0])

conn.close()
