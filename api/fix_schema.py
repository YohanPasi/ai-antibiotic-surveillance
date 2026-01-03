
import psycopg2
import os

DATABASE_URL = os.getenv("DATABASE_URL")

commands = [
    "ALTER TABLE surveillance_logs ADD COLUMN IF NOT EXISTS previous_alert_status VARCHAR(50)",
    "ALTER TABLE surveillance_logs ADD COLUMN IF NOT EXISTS forecast_deviation NUMERIC(5, 2)",
    "ALTER TABLE surveillance_logs ADD COLUMN IF NOT EXISTS consensus_path VARCHAR(100)",
    "ALTER TABLE surveillance_logs ADD COLUMN IF NOT EXISTS baseline_s_percent NUMERIC(5, 2)",
    "ALTER TABLE surveillance_logs ADD COLUMN IF NOT EXISTS alert_reason TEXT",
    "ALTER TABLE surveillance_logs ADD COLUMN IF NOT EXISTS stewardship_prompt TEXT",
    "ALTER TABLE surveillance_logs ADD COLUMN IF NOT EXISTS stewardship_domain VARCHAR(100)",
    "ALTER TABLE surveillance_logs ADD COLUMN IF NOT EXISTS model_version VARCHAR(50)"
]

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    for cmd in commands:
        try:
            print(f"Executing: {cmd}")
            cur.execute(cmd)
            conn.commit()
        except Exception as e:
            print(f"Error on {cmd}: {e}")
            conn.rollback() 
    conn.close()
    print("Schema update complete.")
except Exception as e:
    print(f"Connection Error: {e}")
