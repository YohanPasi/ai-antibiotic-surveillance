import os
from sqlalchemy import create_engine, text

# Get URL from environment (Container's context)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("FATAL: DATABASE_URL not set!")
    exit(1)

print(f"Connecting to DB...")

def apply_schema():
    engine = create_engine(DATABASE_URL)
    
    # Read SQL file (assuming it's copied or we can just embed it if simple, but let's read/embed)
    # Embedding is safer for single-file script execution
    sql = """
    DROP TABLE IF EXISTS master_definitions CASCADE;

    CREATE TABLE IF NOT EXISTS master_definitions (
        id SERIAL PRIMARY KEY,
        category VARCHAR(50) NOT NULL, 
        label VARCHAR(100) NOT NULL,
        value VARCHAR(100) NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(category, value)
    );

    INSERT INTO master_definitions (category, label, value) VALUES
    ('WARD', 'ICU', 'ICU'),
    ('WARD', 'Ward 01', 'Ward 01'),
    ('WARD', 'Ward 02', 'Ward 02'),
    ('WARD', 'OPD', 'Opd'),
    ('WARD', 'A&E', 'A&E'),
    ('WARD', 'O/C', 'O/C'),
    ('WARD', 'Other', 'Other'),
    ('SAMPLE_TYPE', 'Blood', 'Blood'),
    ('SAMPLE_TYPE', 'Urine', 'Urine'),
    ('SAMPLE_TYPE', 'Pus/Wound', 'Pus/Wound'),
    ('SAMPLE_TYPE', 'Sputum', 'Sputum'),
    ('SAMPLE_TYPE', 'Other', 'Other'),
    ('GRAM_STAIN', 'GPC (Cocci)', 'GPC'),
    ('GRAM_STAIN', 'Unknown', 'Unknown')
    ON CONFLICT DO NOTHING;
    """

    print("Executing Master Data Schema Update...")
    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()
    print("✅ Master Data Schema Applied.")

if __name__ == "__main__":
    apply_schema()
