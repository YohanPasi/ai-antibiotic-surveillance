"""Check predictions table schema constraints and nullability."""
import psycopg2
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger('Integrity-Check')

DB_URL = ('postgresql://postgres.zdhvyhijuriggezelyxq:'
          'Yohan%26pasi80253327@aws-1-ap-northeast-2.pooler.supabase.com'
          ':5432/postgres?sslmode=require')

conn = psycopg2.connect(DB_URL)
cursor = conn.cursor()

# 1. Check direction_correct properties
cursor.execute('''
    SELECT column_name, is_nullable, column_default
    FROM information_schema.columns
    WHERE table_name = 'predictions' AND column_name = 'direction_correct'
''')
row = cursor.fetchone()
if row:
    logger.info(f"predictions.direction_correct: NULLABLE={row[1]}, DEFAULT={row[2]}")
else:
    logger.error("direction_correct not found in predictions table")

# 2. Check unique constraints/indexes on predictions
cursor.execute('''
    SELECT
        ix.relname AS index_name,
        a.attname AS column_name
    FROM
        pg_class t,
        pg_class ix,
        pg_index i,
        pg_attribute a
    WHERE
        t.oid = i.indrelid
        AND ix.oid = i.indexrelid
        AND a.attrelid = t.oid
        AND a.attnum = ANY(i.indkey)
        AND t.relkind = 'r'
        AND t.relname = 'predictions'
        AND i.indisunique = true
    ORDER BY
        ix.relname,
        a.attnum
''')
indexes = {}
for idx_name, col_name in cursor.fetchall():
    if idx_name not in indexes:
        indexes[idx_name] = []
    indexes[idx_name].append(col_name)

logger.info(f"Unique indexes on predictions:")
for name, cols in indexes.items():
    logger.info(f"  {name}: {cols}")

cursor.close()
conn.close()
