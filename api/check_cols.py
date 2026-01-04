
import psycopg2
import os

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL not set")
    exit(1)

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'surveillance_logs'")
    cols = [row[0] for row in cur.fetchall()]
    print(f"Columns in surveillance_logs: {cols}")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
