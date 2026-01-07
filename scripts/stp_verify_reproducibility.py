"""
STP Stage 1: Reproducibility Verifier
======================================
Purpose: Verify dataset is bit-for-bit reproducible

Process:
1. Capture current dataset hash
2. Delete all STP tables
3. Re-run pipeline
4. Compare hashes

Database: Supabase PostgreSQL (via DATABASE_URL)
"""

import sys
import os
import argparse
import logging
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

from database import SessionLocal, test_connection
from sqlalchemy import text
from data_processor.stp_stage_1_ingest import ingest_stp_data
from data_processor.stp_wide_to_long_transform import transform_wide_to_long

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if not test_connection():
    logger.error("Database connection failed - check DATABASE_URL")
    sys.exit(1)


def get_dataset_hash(dataset_version: str) -> str:
    """Get current dataset hash from Supabase."""
    session = SessionLocal()
    try:
        result = session.execute(
            text("SELECT source_file_hash FROM stp_dataset_metadata WHERE dataset_version = :v"),
            {"v": dataset_version}
        ).fetchone()
        return result[0] if result else None
    finally:
        session.close()


def clear_stp_tables(dataset_version: str):
    """Clear all STP data for a specific version from Supabase."""
    session = SessionLocal()
    try:
        logger.info(f"Clearing Supabase tables for {dataset_version}...")
        
        session.execute(text("DELETE FROM stp_canonical_long WHERE dataset_version = :v"), {"v": dataset_version})
        session.execute(text("DELETE FROM stp_raw_wide WHERE dataset_version = :v"), {"v": dataset_version})
        session.execute(text("DELETE FROM stp_data_quality_log WHERE dataset_version = :v"), {"v": dataset_version})
        session.execute(text("DELETE FROM stp_antibiotic_registry WHERE dataset_version = :v"), {"v": dataset_version})
        session.execute(text("DELETE FROM stp_governance_declarations WHERE dataset_version = :v"), {"v": dataset_version})
        session.execute(text("DELETE FROM stp_column_provenance WHERE dataset_version = :v"), {"v": dataset_version})
        session.execute(text("DELETE FROM stp_dataset_metadata WHERE dataset_version = :v"), {"v": dataset_version})
        
        session.commit()
        logger.info("✓ Tables cleared")
    finally:
        session.close()


def verify_reproducibility(dataset_version: str = "v1.0.0"):
    """
    Verify dataset reproducibility.
    
    Returns:
        True if reproducible, False otherwise
    """
    logger.info("=" * 70)
    logger.info("STP STAGE 1: REPRODUCIBILITY VERIFICATION")
    logger.info("=" * 70)
    logger.info(f"Dataset Version: {dataset_version}")
    logger.info(f"Database: Supabase")
    logger.info("=" * 70)
    
    # Step 1: Capture original hash
    logger.info("\n[1/4] CAPTURING ORIGINAL DATASET HASH...")
    original_hash = get_dataset_hash(dataset_version)
    
    if not original_hash:
        logger.error(f"❌ Dataset {dataset_version} not found in Supabase")
        return False
    
    logger.info(f"✓ Original Hash: {original_hash[:16]}...")
    
    # Step 2: Clear tables
    logger.info("\n[2/4] CLEARING SUPABASE TABLES...")
    clear_stp_tables(dataset_version)
    
    # Step 3: Re-run pipeline
    logger.info("\n[3/4] RE-RUNNING INGESTION PIPELINE...")
    try:
        ingest_result = ingest_stp_data(dataset_version=dataset_version, force_reload=True)
        transform_result = transform_wide_to_long(dataset_version=dataset_version)
    except Exception as e:
        logger.error(f"❌ Re-ingestion failed: {e}")
        return False
    
    # Step 4: Compare hashes
    logger.info("\n[4/4] COMPARING HASHES...")
    new_hash = get_dataset_hash(dataset_version)
    
    logger.info(f"Original Hash: {original_hash[:16]}...")
    logger.info(f"New Hash:      {new_hash[:16]}...")
    
    if original_hash == new_hash:
        logger.info("\n" + "=" * 70)
        logger.info("✅ REPRODUCIBILITY VERIFIED")
        logger.info("=" * 70)
        logger.info("Dataset is bit-for-bit reproducible")
        logger.info(f"Hash: {original_hash}")
        logger.info("=" * 70)
        return True
    else:
        logger.error("\n" + "=" * 70)
        logger.error("❌ REPRODUCIBILITY FAILED")
        logger.error("=" * 70)
        logger.error("Hashes do not match!")
        logger.error(f"Expected: {original_hash}")
        logger.error(f"Got:      {new_hash}")
        logger.error("=" * 70)
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='STP Stage 1: Reproducibility Verifier')
    parser.add_argument('--version', type=str, default='v1.0.0', help='Dataset version')
    args = parser.parse_args()
    
    success = verify_reproducibility(dataset_version=args.version)
    sys.exit(0 if success else 1)
