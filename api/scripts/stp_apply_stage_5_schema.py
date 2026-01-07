
import sys
import os
import psycopg2
import logging

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from api.database import DATABASE_URL
except ImportError:
    # If standard import fails, try to get it directly or define fallback
    # This often happens if 'api' isn't treated as a package in some contexts
    # Let's try importing database from the api folder directly if added to path
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'api'))
    from database import DATABASE_URL

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def apply_schema():
    """
    Applies the Stage 5 Operational Schema to the database.
    Including M73 Migration (registry update).
    """
    schema_path = os.path.join(os.path.dirname(__file__), '../database/create_stp_stage_5_schema.sql')
    
    if not os.path.exists(schema_path):
        logger.error(f"Schema file not found at: {schema_path}")
        return

    try:
        logger.info(f"Reading schema from: {schema_path}")
        with open(schema_path, 'r') as f:
            sql_script = f.read()

        logger.info("Connecting to database...")
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True  # Important for some DDL, though here transaction is fine
        cursor = conn.cursor()

        logger.info("Applying Stage 5 schema...")
        cursor.execute(sql_script)
        
        logger.info("✅ Stage 5 Schema Applied Successfully (Operational Layer Ready).")

        cursor.close()
        conn.close()

    except Exception as e:
        logger.error(f"Failed to apply schema: {e}")
        raise

if __name__ == "__main__":
    apply_schema()
