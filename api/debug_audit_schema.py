import os
import pandas as pd
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "postgresql://postgres.zdhvyhijuriggezelyxq:Yohan%26pasi80253327@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres"

engine = create_engine(DATABASE_URL)
with engine.begin() as connection:
    connection.execute(text("ALTER TABLE beta_lactam_audit_logs ALTER COLUMN clinician_override TYPE VARCHAR(100);"))
    connection.execute(text("ALTER TABLE beta_lactam_audit_logs ALTER COLUMN traffic_light_summary TYPE VARCHAR(50);"))

print("Schema alteration successful!")
