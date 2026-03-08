from database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
res = db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'ast_manual_entry'")).fetchall()
for r in res: print(f"{r[0]} ({r[1]})")
db.close()
