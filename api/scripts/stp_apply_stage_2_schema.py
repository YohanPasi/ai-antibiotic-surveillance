
import os
import sys
from pathlib import Path
import logging
from sqlalchemy import text

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from api.database import get_db, SessionLocal, engine
except ImportError:
    try:
        from database import get_db, SessionLocal, engine
    except ImportError:
        # Fallback for when running from root
        sys.path.append(os.getcwd())
        from database import get_db, SessionLocal, engine

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def apply_schema():
    """Applies the Stage 2 schema SQL to the database."""
    schema_path = Path("database/create_stp_stage_2_schema.sql")
    
    if not schema_path.exists():
        logger.error(f"Schema file not found at {schema_path}")
        return False
        
    logger.info(f"Reading schema from {schema_path}")
    try:
        with open(schema_path, "r") as f:
            sql_content = f.read()
    except Exception as e:
        logger.error(f"Failed to read schema file: {e}")
        return False

    logger.info("Connecting to database...")
    try:
        # Use a raw connection to execute the script
        # This is often safer for large SQL scripts with multiple statements
        with engine.connect() as connection:
            logger.info("Executing SQL schema...")
            # Split by statement if needed, or just execute the block. 
            # SQLAlchemy text() executable might handle blocks depending on the driver,
            # but usually it's better to execute as a single block for Postgres.
            connection.execute(text(sql_content))
            connection.commit()
            logger.info("Schema applied successfully!")
            return True
            
    except Exception as e:
        logger.error(f"Database execution failed: {e}")
        return False

if __name__ == "__main__":
    success = apply_schema()
    if success:
        sys.exit(0)
    else:
        sys.exit(1)
