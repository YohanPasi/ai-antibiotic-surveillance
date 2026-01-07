"""
STP Stage 1: Dataset Freeze Tool
=================================
Purpose: M6 - Mark dataset as immutable

Usage:
    python scripts/stp_freeze_dataset.py --version v1.0.0 --approved-by "navod"

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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if not test_connection():
    logger.error("Database connection failed - check DATABASE_URL")
    sys.exit(1)


def freeze_dataset(dataset_version: str, approved_by: str):
    """
    M6: Mark dataset as FROZEN (immutable).
    
    Args:
        dataset_version: Version to freeze
        approved_by: Username of approver
    
    Returns:
        True if successful, False otherwise
    """
    logger.info("=" * 70)
    logger.info("STP STAGE 1: DATASET FREEZE TOOL (M6)")
    logger.info("=" * 70)
    logger.info(f"Dataset Version: {dataset_version}")
    logger.info(f"Approved By: {approved_by}")
    logger.info(f"Database: Supabase")
    logger.info("=" * 70)
    
    session = SessionLocal()
    
    try:
        # Check if dataset exists
        logger.info("\n[1/3] Checking dataset exists...")
        metadata = session.execute(
            text("""
                SELECT is_frozen, total_rows_accepted 
                FROM stp_dataset_metadata 
                WHERE dataset_version = :v
            """),
            {"v": dataset_version}
        ).fetchone()
        
        if not metadata:
            logger.error(f"❌ Dataset {dataset_version} not found in Supabase")
            return False
        
        is_frozen, total_rows = metadata
        
        if is_frozen:
            logger.warning(f"⚠️ Dataset {dataset_version} is already frozen")
            logger.info("   No action taken")
            return True
        
        logger.info(f"✓ Dataset found: {total_rows:,} isolates")
        
        # Confirm freeze
        logger.info("\n[2/3] Freezing dataset...")
        logger.warning("⚠️  This action is IRREVERSIBLE")
        logger.warning("   Once frozen, this dataset cannot be modified")
        
        # In production, add confirmation prompt here
        # For automation, proceed directly
        
        # Freeze the dataset
        session.execute(
            text("""
                UPDATE stp_dataset_metadata
                SET is_frozen = TRUE,
                    approved_at = NOW(),
                    approved_by = :approved_by
                WHERE dataset_version = :v
            """),
            {"v": dataset_version, "approved_by": approved_by}
        )
        
        session.commit()
        
        logger.info("✓ Dataset frozen in Supabase")
        
        # Verify freeze
        logger.info("\n[3/3] Verifying freeze status...")
        result = session.execute(
            text("""
                SELECT is_frozen, approved_at, approved_by 
                FROM stp_dataset_metadata 
                WHERE dataset_version = :v
            """),
            {"v": dataset_version}
        ).fetchone()
        
        if result and result[0]:
            logger.info("=" * 70)
            logger.info("✅ DATASET FROZEN SUCCESSFULLY")
            logger.info("=" * 70)
            logger.info(f"Version: {dataset_version}")
            logger.info(f"Approved By: {result[2]}")
            logger.info(f"Approved At: {result[1]}")
            logger.info(f"Status: IMMUTABLE")
            logger.info("=" * 70)
            logger.info("\n📋 Implications:")
            logger.info("  • This dataset version cannot be overwritten")
            logger.info("  • Any re-processing requires a new version (e.g., v1.0.1)")
            logger.info("  • M6 freeze policy is now enforced")
            logger.info("=" * 70)
            return True
        else:
            logger.error("❌ Freeze verification failed")
            return False
    
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Freeze failed: {e}")
        return False
    
    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='STP Stage 1: Dataset Freeze Tool (M6)'
    )
    parser.add_argument(
        '--version',
        type=str,
        required=True,
        help='Dataset version to freeze (e.g., v1.0.0)'
    )
    parser.add_argument(
        '--approved-by',
        type=str,
        required=True,
        help='Username of person approving freeze'
    )
    parser.add_argument(
        '--confirm',
        action='store_true',
        help='Skip confirmation prompt (for automation)'
    )
    
    args = parser.parse_args()
    
    success = freeze_dataset(
        dataset_version=args.version,
        approved_by=args.approved_by
    )
    
    sys.exit(0 if success else 1)
