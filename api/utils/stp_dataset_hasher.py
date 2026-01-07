"""
STP Stage 1: Dataset Hasher & Version Control
==============================================
Purpose: Cryptographic integrity verification

Features:
- SHA-256 file hashing
- Dataset versioning (semantic)
- M5: Schema checksum tracking
- Reproducibility proof
"""

import hashlib
import os
from typing import Dict
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def compute_file_hash(filepath: str) -> str:
    """
    Compute SHA-256 hash of file.
    
    Used for:
    - Source Excel file verification
    - Schema file verification (M5)
    - Reproducibility proof
    """
    sha256_hash = hashlib.sha256()
    
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    return sha256_hash.hexdigest()


def compute_schema_hash(schema_file: str = None) -> str:
    """
    M5: Compute SHA-256 hash of schema SQL file.
    
    Enables:
    - Schema version tracking
    - Migration verification
    - Reproducibility
    """
    if schema_file is None:
        schema_file = os.path.join(
            os.path.dirname(__file__),
            '../../database/create_stp_stage_1_schema.sql'
        )
    
    if not os.path.exists(schema_file):
        logger.warning(f"Schema file not found: {schema_file}")
        return "NOT_COMPUTED"
    
    return compute_file_hash(schema_file)


def increment_version(current_version: str) -> str:
    """
    Increment semantic version.
    
    Examples:
        v1.0.0 → v1.0.1 (patch)
        v1.0.0 → v1.1.0 (minor, if force_reload)
    """
    if not current_version.startswith('v'):
        current_version = f'v{current_version}'
    
    parts = current_version[1:].split('.')
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    
    # Increment patch version
    patch += 1
    
    return f'v{major}.{minor}.{patch}'


def verify_dataset_integrity(source_file: str, expected_hash: str) -> bool:
    """
    Verify dataset hasn't changed.
    
    Returns:
        True if hash matches, False otherwise
    """
    actual_hash = compute_file_hash(source_file)
    return actual_hash == expected_hash


def generate_hash_report(source_file: str, schema_file: str = None) -> Dict:
    """
    Generate complete hash report for reproducibility.
    
    Returns:
        Dictionary with all relevant hashes
    """
    report = {
        'source_file': os.path.basename(source_file),
        'source_file_hash': compute_file_hash(source_file),
        'schema_version': '1.0.0',
        'schema_hash': compute_schema_hash(schema_file)
    }
    
    logger.info("Hash Report Generated:")
    logger.info(f"  Source: {report['source_file']}")
    logger.info(f"  Source SHA-256: {report['source_file_hash'][:16]}...")
    logger.info(f"  Schema Version: {report['schema_version']}")
    logger.info(f"  Schema SHA-256: {report['schema_hash'][:16]}...")
    
    return report


if __name__ == "__main__":
    # Example usage
    source = "../../Raw/Streptococcus_Enterococcus_AST_WIDE_12000_ExpandedWards.xlsx"
    schema = "../../database/create_stp_stage_1_schema.sql"
    
    report = generate_hash_report(source, schema)
    print(f"\nFull Report: {report}")
