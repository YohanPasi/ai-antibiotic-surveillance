import os
import pandas as pd
from sqlalchemy import create_engine

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "postgresql://postgres.zdhvyhijuriggezelyxq:Yohan%26pasi80253327@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres"

engine = create_engine(DATABASE_URL)
print("beta_lactam_encounters:")
print(pd.read_sql("SELECT * FROM beta_lactam_encounters LIMIT 1", engine).columns)
print("----------------")
print("beta_lactam_lab_results:")
print(pd.read_sql("SELECT * FROM beta_lactam_lab_results LIMIT 1", engine).columns)
