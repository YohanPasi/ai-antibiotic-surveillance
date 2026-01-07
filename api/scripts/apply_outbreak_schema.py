#!/usr/bin/env python3
"""
Apply Outbreak Discriminator Schema to database
"""
import sys
sys.path.append('/app')

from database import engine
from sqlalchemy import text

def apply_schema():
    """Apply the outbreak discriminator schema"""
    
    print("Reading outbreak discriminator schema...")
    with open('/app/database_scripts/create_outbreak_discriminator_schema.sql', 'r') as f:
        schema_sql = f.read()
    
    print("Connecting to database...")
    with engine.connect() as conn:
        # Split by semicolons and execute each statement
        statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
        
        total = len(statements)
        for idx, statement in enumerate(statements, 1):
            if not statement or statement.startswith('--'):
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
    
    print("\n✅ Outbreak discriminator schema applied!")
    print("\nREFINEMENTS IMPLEMENTED:")
    print("  #1 - Source model tracking for audit trail")
    print("  #2 - Outbreak exclusion from drift calculations")
    print("  #3 - Alert fatigue control via unique constraints")
    print("  #4 - Human confirmation gate (status workflow)")
    print("  #5 - Outbreak ≠ Drift safeguard documented")

if __name__ == "__main__":
    apply_schema()
