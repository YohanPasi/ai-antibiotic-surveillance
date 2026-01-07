"""
STP Stage 1: Wide-to-Long Transformation
==========================================
Purpose: Transform wide AST format to canonical long format

Input: stp_raw_wide (one row per isolate)
Output: stp_canonical_long (one row per AST test)

Transformation:
- Each antibiotic column becomes a separate row
- Metadata (organism, ward, date) carried forward
- NA values preserved (M2: "Not Tested", not missing)
- No aggregation (Stage 1 firewall - M10)
"""

import logging
from sqlalchemy import text
import os
import json
import sys

# Use existing database connection
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from database import SessionLocal

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def transform_wide_to_long(dataset_version: str = "v1.0.0"):
    """
    Transform wide AST data to canonical long format.
    
    Process:
    1. Read from stp_raw_wide
    2. Unpack antibiotic_results JSONB
    3. Create one row per antibiotic test
    4. Insert to stp_canonical_long
    
    M2: NA values preserved (means "Not Tested")
    M10: No aggregation (Stage 1 boundary)
    """
    logger.info("=" * 60)
    logger.info("STP STAGE 1: WIDE-TO-LONG TRANSFORMATION")
    logger.info("=" * 60)
    
    session = SessionLocal()
    
    try:
        # Get raw connection for performance (bypass SQLAlchemy ORM overhead)
        # We need psycopg2 cursor for execute_values
        conn = session.connection().connection
        # If using pool, we might need to ensure we have a valid raw connection
        # Alternatively, create a new raw connection using engine
        if not conn:
             from database import engine
             conn = engine.raw_connection()
             
        # Enable autocommit or manage transaction manually?
        # psycopg2 connection from sqlalchemy might be inside a transaction
        
        with conn.cursor() as cur:
             # 1. Clear existing data
             logger.info(f"Clearing existing data for {dataset_version}...")
             cur.execute("DELETE FROM stp_canonical_long WHERE dataset_version = %s", (dataset_version,))
             
             # 2. Get total rows for progress
             cur.execute("SELECT COUNT(*) FROM stp_raw_wide WHERE dataset_version = %s", (dataset_version,))
             total_rows = cur.fetchone()[0]
             logger.info(f"Found {total_rows} isolates to transform.")
             
             chunk_size = 500
             total_tests = 0
             
             for chunk_start in range(0, total_rows, chunk_size):
                 # Fetch Chunk
                 cur.execute(f"""
                    SELECT isolate_id, sample_date, organism, ward, sample_type, antibiotic_results
                    FROM stp_raw_wide
                    WHERE dataset_version = %s
                    ORDER BY isolate_id
                    LIMIT %s OFFSET %s
                 """, (dataset_version, chunk_size, chunk_start))
                 
                 rows = cur.fetchall()
                 long_batch = []
                 
                 for row in rows:
                     isolate_id, sample_date, organism, ward, sample_type, antibiotic_results = row
                     
                     # Check if JSON string or dict
                     if isinstance(antibiotic_results, str):
                         ab_dict = json.loads(antibiotic_results)
                     else:
                         ab_dict = antibiotic_results
                         
                     if not ab_dict: continue

                     for antibiotic, ast_result in ab_dict.items():
                         if ast_result and ast_result != 'NA':
                             long_batch.append((
                                 isolate_id, sample_date, organism, ward, sample_type,
                                 antibiotic, ast_result, dataset_version
                             ))
                 
                 # Bulk Insert
                 if long_batch:
                     from psycopg2.extras import execute_values
                     execute_values(
                        cur,
                        """
                        INSERT INTO stp_canonical_long (
                            isolate_id, sample_date, organism, ward, sample_type,
                            antibiotic, ast_result, dataset_version
                        ) VALUES %s
                        """,
                        long_batch
                     )
                     total_tests += len(long_batch)
                     
                 # Commit per chunk if needed, or wait for end?
                 # If we are in a transaction block from session, we might need to be careful.
                 # Safe to just let the main session commit? 
                 # Wait, raw connection might be separate if from engine.raw_connection().
                 # If from session.connection().connection, it shares transaction.
        
        session.commit()
        
        logger.info("-" * 60)
        logger.info(f"✓ TRANSFORMATION COMPLETE (Optimized)")
        logger.info(f"  Isolates: {total_rows}")
        logger.info(f"  AST tests: {total_tests}")
        logger.info("-" * 60)
        
        return {
            "status": "success",
            "isolates": total_rows,
            "ast_tests": total_tests,
            "dataset_version": dataset_version
        }

    except Exception as e:
        session.rollback()
        logger.error(f"❌ Transformation failed: {e}")
        raise e
    
    finally:
        session.close()


def insert_long_batch(session, batch):
    """Insert batch into stp_canonical_long."""
    for row in batch:
        session.execute(
            text("""
                INSERT INTO stp_canonical_long (
                    isolate_id, sample_date, organism, ward, sample_type,
                    antibiotic, ast_result, dataset_version
                ) VALUES (
                    :isolate_id, :sample_date, :organism, :ward, :sample_type,
                    :antibiotic, :ast_result, :dataset_version
                )
            """),
            row
        )


if __name__ == "__main__":
    result = transform_wide_to_long(dataset_version="v1.0.0")
    print(f"\nResult: {result}")
