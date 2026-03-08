import os, psycopg2
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

cur.execute('SELECT COUNT(*) FROM forecast_validation_log;')
val_count = cur.fetchone()[0]

cur.execute('SELECT COUNT(*) FROM predictions WHERE validated_at IS NOT NULL;')
pred_val_count = cur.fetchone()[0]

print(f"Total row count in forecast_validation_log: {val_count}")
print(f"Total predictions marked validated: {pred_val_count}")

cur.execute('''
    SELECT ward, organism, antibiotic, forecast_week, predicted_s_percent, actual_s_percent, prediction_error 
    FROM forecast_validation_log
    LIMIT 10;
''')
print("\nSample validations:")
for row in cur.fetchall():
    print(row)

conn.close()
