from database import SessionLocal
from sqlalchemy import text

def drop_and_recreate():
    """
    Drop old JSONB-based table and recreate with proper columns.
    WARNING: This will delete existing data!
    """
    print("⚠️  WARNING: This will drop the existing esbl_encounters table!")
    print("   All data will be lost. Press Ctrl+C to cancel...")
    
    import time
    time.sleep(3)
    
    db = SessionLocal()
    try:
        # Drop old table
        print("🗑️  Dropping old table...")
        db.execute(text("DROP TABLE IF EXISTS esbl_encounters CASCADE"))
        db.commit()
        
        # Read and execute new schema
        print("📄 Creating new table with explicit columns...")
        with open("c:\\Users\\YohanN\\Desktop\\Project Thenula\\ai-antibiotic-surveillance\\database\\create_esbl_encounters.sql", "r") as f:
            sql = f.read()
        
        db.execute(text(sql))
        db.commit()
        
        print("✅ Table recreated successfully!")
        print("\nNew columns:")
        print("  - encounter_id (PK)")
        print("  - age, gender, ward")
        print("  - organism, gram_stain, sample_type")
        print("  - esbl_probability, risk_group")
        print("  - recommendations (JSONB for drug list)")
        print("  - And more... check the schema file!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    drop_and_recreate()
