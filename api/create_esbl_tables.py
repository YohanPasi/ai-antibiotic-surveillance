from database import SessionLocal
from sqlalchemy import text
import os

def create_tables():
    print("🚀 applying ESBL Schema Extensions...")
    db = SessionLocal()
    try:
        # Load SQL
        sql_path = "../database/create_esbl_encounters.sql"
        if not os.path.exists(sql_path):
             # Try absolute path fallback if running from different cwd
             sql_path = "c:\\Users\\YohanN\\Desktop\\Project Thenula\\ai-antibiotic-surveillance\\database\\create_esbl_encounters.sql"
        
        with open(sql_path, "r") as f:
            sql_script = f.read()

        # Execute
        print(f"   Executing {sql_path}...")
        db.execute(text(sql_script))
        db.commit()
        print("✅ ESBL Tables Created Successfully.")
        
    except Exception as e:
        print(f"❌ Error applying schema: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_tables()
