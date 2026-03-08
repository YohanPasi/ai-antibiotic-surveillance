import os, psycopg2
from psycopg2.errors import DuplicateObject, DuplicateTable

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
conn.autocommit = True
cur = conn.cursor()

commands = [c.strip() for c in open('/app/temp_schema.sql').read().split(';') if c.strip()]
for cmd in commands:
    try:
        cur.execute(cmd)
    except (DuplicateObject, DuplicateTable) as e:
        pass
    except Exception as e:
        print(f'Error executing {cmd[:50]}...: {e}')

print('Schema applied with graceful error handling.')
