import os, psycopg2
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

cur.execute('''
    SELECT organism, antibiotic, COUNT(*) 
    FROM ast_raw_data 
    WHERE culture_date >= '2026-03-02'
    GROUP BY organism, antibiotic
''')
print("Recent physical isolates entered:")
for row in cur.fetchall():
    print(row)

conn.close()
