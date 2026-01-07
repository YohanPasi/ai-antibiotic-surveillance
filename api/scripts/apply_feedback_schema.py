#!/usr/bin/env python3
"""
Apply STP Feedback Loop schema to database
"""
import sys
sys.path.append('/app')

from database import engine
from sqlalchemy import text

def apply_schema():
    """Apply the feedback loop schema"""
    
    print("Reading schema file...")
    with open('/app/database_scripts/create_stp_feedback_schema.sql', 'r') as f:
        schema_sql = f.read()
    
    print("Connecting to database...")
    with engine.connect() as conn:
        # Split by semicolons and execute each statement
        statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
        
        total = len(statements)
        for idx, statement in enumerate(statements, 1):
            if not statement:
                continue
                
            try:
                print(f"Executing statement {idx}/{total}...")
                conn.execute(text(statement))
                conn.commit()
            except Exception as e:
                error_msg = str(e)
                # Ignore "already exists" errors
                if 'already exists' in error_msg.lower():
                    print(f"  ⚠️ Skipped (already exists)")
                else:
                    print(f"  ❌ Error: {error_msg[:200]}")
                    conn.rollback()
    
    print("\n✅ Schema application complete!")

if __name__ == "__main__":
    apply_schema()
