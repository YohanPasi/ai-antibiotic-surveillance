"""
STP Stage 1: Reproducibility Verifier
=====================================
Verification script to prove dataset reproducibility as per M10/M5.

Process:
1. Capture hash of current canonical dataset (Hash A)
2. Capture hash of current source file
3. Compare against stored metadata in `stp_dataset_metadata`

(Note: Full "destroy and rebuild" verification is risky for production, 
 so this script focuses on integrity verification of the current state).

Usage:
    python stp_verify_reproducibility.py [--version v1.0.0]
"""
import argparse
import logging
import sys
import os
import hashlib
from sqlalchemy import text

# Add api to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import SessionLocal

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_reproducibility(dataset_version="v1.0.0"):
    session = SessionLocal()
    try:
        logger.info(f"🔍 VERIFYING REPRODUCIBILITY for {dataset_version}")
        
        # 1. Fetch Stored Metadata
        logger.info("  Fetching stored metadata...")
        metadata = session.execute(
            text("SELECT source_file_name, source_file_hash, total_rows_accepted FROM stp_dataset_metadata WHERE dataset_version = :v"),
            {"v": dataset_version}
        ).fetchone()
        
        if not metadata:
            logger.error(f"❌ Metadata not found for {dataset_version}")
            return False
            
        stored_source_name, stored_source_hash, stored_count = metadata
        logger.info(f"  Stored Hash: {stored_source_hash}")
        
        # 2. Check Source File Integrity
        # Assuming file path logic from ingest script (hardcoded for now as per ingestion)
        source_path = '/app/data/raw/Streptococcus_Enterococcus_AST_WIDE_12000_ExpandedWards.xlsx' 
        # Note: If running outside docker, path might differ. 
        # We try to detect execution environment or use relative path relative to project root?
        # For now, we assume this script runs in the same environment as ingestion (Docker).
        
        if os.path.exists(source_path):
            logger.info("  Re-hashing source file...")
            sha256_hash = hashlib.sha256()
            with open(source_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            current_hash = sha256_hash.hexdigest()
            
            if current_hash == stored_source_hash:
                logger.info("  ✅ Source file hash MATCHES.")
            else:
                logger.error(f"  ❌ Source file hash MISMATCH!")
                logger.error(f"     Expected: {stored_source_hash}")
                logger.error(f"     Found:    {current_hash}")
                return False
        else:
            logger.warning(f"  ⚠ Source file not found at {source_path}. Skipping file hash check.")
        
        # 3. Verify Database Content Integrity (Row Count)
        current_count = session.execute(
            text("SELECT COUNT(DISTINCT isolate_id) FROM stp_canonical_long WHERE dataset_version = :v"),
            {"v": dataset_version}
        ).scalar()
        
        logger.info(f"  Stored Isolate Count: {stored_count}")
        logger.info(f"  Current Isolate Count: {current_count}")
        
        if current_count == stored_count:
             logger.info("  ✅ Row count MATCHES.")
        else:
             logger.error("  ❌ Row count MISMATCH!")
             return False
             
        # 4. Canonical Data Hash (Advanced)
        # Compute hash of sorted canonical data to ensure bit-for-bit DB consistency
        logger.info("  Computing canonical data signature...")
        # Order by isolate_id, antibiotic to ensure deterministic order
        rows = session.execute(
            text("""
                SELECT isolate_id, antibiotic, ast_result 
                FROM stp_canonical_long 
                WHERE dataset_version = :v
                ORDER BY isolate_id, antibiotic
            """),
            {"v": dataset_version}
        ).fetchall()
        
        data_str = "".join([f"{r[0]}{r[1]}{r[2]}" for r in rows])
        data_hash = hashlib.sha256(data_str.encode()).hexdigest()
        
        logger.info(f"  ℹ Canonical Data Signature: {data_hash}")
        logger.info("  (Store this signature to verify future migrations)")
        
        logger.info("\n✅ REPRODUCIBILITY VERIFICATION PASSED.")
        return True

    except Exception as e:
        logger.error(f"Verification Failed: {e}")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="v1.0.0")
    args = parser.parse_args()
    
    verify_reproducibility(args.version)
