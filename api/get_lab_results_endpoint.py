from database import SessionLocal
from sqlalchemy import text
import os

def create_esbl_tables():
    print("🚀 Creating ESBL-Specific Tables...")
    db = SessionLocal()
    
    sql_files = [
        "create_esbl_encounters.sql",
        "create_esbl_audit_logs.sql",
        "create_esbl_lab_results.sql"
    ]
    
    base_path = "c:\\Users\\YohanN\\Desktop\\Project Thenula\\ai-antibiotic-surveillance\\database\\"
    
    try:
        for sql_file in sql_files:
            file_path = os.path.join(base_path, sql_file)
            
            print(f"   📄 Executing {sql_file}...")
            with open(file_path, "r") as f:
                sql_script = f.read()
            
            db.execute(text(sql_script))
            db.commit()
            print(f"   ✅ {sql_file} applied successfully.")
        
        print("\n✅ ALL ESBL Tables Created Successfully!")
        print("\nESBL Tables:")
        print("  1. esbl_encounters - Draft/Session storage")
        print("  2. esbl_audit_logs - Governance logs")
        print("  3. esbl_lab_results - Final lab results")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_esbl_tables()
