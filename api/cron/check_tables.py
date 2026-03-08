"""Inspect model_performance schema for Phase 3B."""
import psycopg2

DB_URL = ('postgresql://postgres.zdhvyhijuriggezelyxq:'
          'Yohan%26pasi80253327@aws-1-ap-northeast-2.pooler.supabase.com'
          ':5432/postgres?sslmode=require')

conn = psycopg2.connect(DB_URL)
cursor = conn.cursor()

# 1. All columns
cursor.execute("""
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns
    WHERE table_name = 'model_performance'
    ORDER BY ordinal_position
""")
print("model_performance columns:")
for r in cursor.fetchall():
    print(f"  {r[0]:35s}  {r[1]:25s}  nullable={r[2]}  default={r[3]}")

# 2. Constraints / unique indexes
cursor.execute("""
    SELECT ix.relname AS index_name, i.indisunique, i.indisprimary,
           array_agg(a.attname ORDER BY a.attnum) AS columns
    FROM pg_class t
    JOIN pg_index i ON t.oid = i.indrelid
    JOIN pg_class ix ON ix.oid = i.indexrelid
    JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(i.indkey)
    WHERE t.relname = 'model_performance'
    GROUP BY ix.relname, i.indisunique, i.indisprimary
""")
print("\nIndexes / constraints on model_performance:")
for r in cursor.fetchall():
    print(f"  {r[0]:40s}  unique={r[1]}  pk={r[2]}  cols={r[3]}")

# 3. Sample row
cursor.execute("SELECT * FROM model_performance LIMIT 1")
if cursor.description:
    cols = [d[0] for d in cursor.description]
    row  = cursor.fetchone()
    print("\nSample row:")
    if row:
        for k, v in zip(cols, row):
            print(f"  {k}: {v}")
    else:
        print("  (table is empty)")

cursor.close()
conn.close()
