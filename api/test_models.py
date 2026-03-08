import os, psycopg2
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM stp_model_registry;")
reg_count = cur.fetchone()[0]

cur.execute("SELECT model_type, COUNT(*) FROM stp_model_registry GROUP BY model_type;")
types = cur.fetchall()

cur.execute("SELECT model_name, COUNT(*) FROM model_performance GROUP BY model_name;")
perf = cur.fetchall()

print('Registry Rows:', reg_count)
print('Model Types in Registry:', types)
print('Models in Performance Table:', perf)

conn.close()
