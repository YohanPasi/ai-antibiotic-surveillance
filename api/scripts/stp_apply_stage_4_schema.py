
"""
STP Stage 4: Schema Application Script
-------------------------------------
Applies the Stage 4 schema (Model Evaluation) to the database.
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
    from api.database import DATABASE_URL
except ImportError:
    try:
        from database import DATABASE_URL
    except ImportError:
        logger.error("Could not import DATABASE_URL. Ensure PYTHONPATH is set.")
        sys.exit(1)

def apply_stage_4_schema():
    """Reads SQL file and executes it against the database."""
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sql_path = os.path.join(base_dir, "database", "create_stp_stage_4_schema.sql")
    
    if not os.path.exists(sql_path):
        logger.error(f"Schema file not found at: {sql_path}")
        sys.exit(1)
        
    logger.info(f"Reading schema from: {sql_path}")
    
    with open(sql_path, "r") as f:
        sql_content = f.read()
        
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            logger.info("Connected to database. Applying Stage 4 schema...")
            connection.execute(text(sql_content))
            connection.commit()
            logger.info("✅ Stage 4 Schema Applied Successfully.")
            
    except Exception as e:
        logger.error(f"Failed to apply schema: {e}")
        sys.exit(1)

if __name__ == "__main__":
    apply_stage_4_schema()
