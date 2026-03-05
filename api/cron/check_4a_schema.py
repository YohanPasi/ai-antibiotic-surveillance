"""Inspect model_performance schema for Phase 4A migration planning."""
import psycopg2

DB_URL = ('postgresql://postgres.zdhvyhijuriggezelyxq:'
          'Yohan%26pasi80253327@aws-1-ap-northeast-2.pooler.supabase.com'
          ':5432/postgres?sslmode=require')

conn   = psycopg2.connect(DB_URL)
cursor = conn.cursor()

cursor.execute("""
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns
    WHERE table_name = 'model_performance'
    ORDER BY ordinal_position
""")
print("model_performance columns:")
for r in cursor.fetchall():
    print(f"  {r[0]:40s}  {r[1]:25s}  nullable={r[2]}  default={r[3]}")

cursor.execute("""
    SELECT ix.relname AS index_name, i.indisunique,
           array_agg(a.attname ORDER BY a.attnum) AS columns
    FROM pg_class t
    JOIN pg_index i ON t.oid = i.indrelid
    JOIN pg_class ix ON ix.oid = i.indexrelid
    JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(i.indkey)
    WHERE t.relname = 'model_performance'
    GROUP BY ix.relname, i.indisunique
""")
print("\nIndexes:")
for r in cursor.fetchall():
    print(f"  {r[0]:55s}  unique={r[1]}  cols={r[2]}")

# Also check ast_weekly_aggregated for reference on history query
cursor.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'ast_weekly_aggregated'
    ORDER BY ordinal_position
    LIMIT 15
""")
print("\nast_weekly_aggregated columns:")
for r in cursor.fetchall():
    print(f"  {r[0]:40s}  {r[1]}")

cursor.close()
conn.close()
