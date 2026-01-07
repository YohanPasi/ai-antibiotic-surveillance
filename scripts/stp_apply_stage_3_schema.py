
"""
STP Stage 3: Schema Application Script
-------------------------------------
Applies the Stage 3 schema (Predictive Modeling) to the database.
Handles tables: stp_model_registry, stp_model_predictions, 
stp_model_explanations, stp_early_warnings, stp_model_drift_metrics.
"""

import os
import sys
import logging
from sqlalchemy import text, create_engine

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path to import database module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Try importing from api.database first (Docker structure)
    from api.database import DATABASE_URL
except ImportError:
    # Fallback for local execution if api package not resolved
    try:
        from database import DATABASE_URL
    except ImportError:
        # Final fallback - manual constructed URL or hard fail
        logger.error("Could not import DATABASE_URL. Ensure PYTHONPATH is set.")
        sys.exit(1)

def get_db_url():
    return DATABASE_URL

def apply_stage_3_schema():
    """Reads SQL file and executes it against the database."""
    
    # 1. Locate SQL file
    # Assuming script is in scripts/ and SQL is in database/
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sql_path = os.path.join(base_dir, "database", "create_stp_stage_3_schema.sql")
    
    if not os.path.exists(sql_path):
        logger.error(f"Schema file not found at: {sql_path}")
        sys.exit(1)
        
    logger.info(f"Reading schema from: {sql_path}")
    
    with open(sql_path, "r") as f:
        sql_content = f.read()
        
    # 2. Connect to DB
    # We use raw connection for DDL usually, or engine.connect()
    try:
        # Use session mode URL (port 6543) if possible for DDL, but transaction pooling (6543) 
        # doesn't support prepared statements well. DDL is fine.
        # However, for schema changes, direct connection is safer if pooling is aggressive.
        
        # Let's get the standard URL
        db_url = get_db_url()
        engine = create_engine(db_url)
        
        with engine.connect() as connection:
            logger.info("Connected to database. Applying schema...")
            
            # Split by statement if needed, or execute block if simple
            # SQLAlchemy execute(text()) can handle multiple statements if supported by driver
            # But safer to execute as one block if pure SQL script
            
            connection.execute(text(sql_content))
            connection.commit()
            
            logger.info("✅ Stage 3 Schema Applied Successfully.")
            
    except Exception as e:
        logger.error(f"Failed to apply schema: {e}")
        sys.exit(1)

if __name__ == "__main__":
    apply_stage_3_schema()
