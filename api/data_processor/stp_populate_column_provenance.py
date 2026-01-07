"""
STP Stage 1: Column Provenance Populator
=========================================
Purpose: M7 - Document column-level lineage (raw vs derived vs normalized)

Populates stp_column_provenance table with metadata about each column's origin.

Publication Impact: Demonstrates transparency about data transformations
"""

import logging
from sqlalchemy import text
import os
import sys

# Use existing database connection
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from database import SessionLocal

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# M7: Column provenance definitions
COLUMN_PROVENANCE = [
    # stp_canonical_long (main output table)
    {
        'table_name': 'stp_canonical_long',
        'column_name': 'isolate_id',
        'origin': 'raw',
        'description': 'Laboratory isolate identifier (Lab_No from source)',
        'transformation_logic': 'Direct from Excel Lab_No column, stripped whitespace',
        'introduced_in_stage': 1
    },
    {
        'table_name': 'stp_canonical_long',
        'column_name': 'sample_date',
        'origin': 'raw',
        'description': 'Specimen collection date',
        'transformation_logic': 'Direct from Excel Date column, validated as date type',
        'introduced_in_stage': 1
    },
    {
        'table_name': 'stp_canonical_long',
        'column_name': 'organism',
        'origin': 'normalized',
        'description': 'Canonical organism name',
        'transformation_logic': 'Normalized via ORGANISM_NORMALIZATION_MAP dictionary in stp_stage_1_ingest.py',
        'introduced_in_stage': 1
    },
    {
        'table_name': 'stp_canonical_long',
        'column_name': 'ward',
        'origin': 'normalized',
        'description': 'Canonical ward name',
        'transformation_logic': 'Matched to stp_ward_taxonomy table, Unknown if not found',
        'introduced_in_stage': 1
    },
    {
        'table_name': 'stp_canonical_long',
        'column_name': 'sample_type',
        'origin': 'raw',
        'description': 'Specimen type',
        'transformation_logic': 'Direct from Excel Sample Type column, trimmed',
        'introduced_in_stage': 1
    },
    {
        'table_name': 'stp_canonical_long',
        'column_name': 'antibiotic',
        'origin': 'derived',
        'description': 'Antibiotic tested',
        'transformation_logic': 'Extracted from Excel column headers pattern: Antibiotic [Name]',
        'introduced_in_stage': 1
    },
    {
        'table_name': 'stp_canonical_long',
        'column_name': 'ast_result',
        'origin': 'normalized',
        'description': 'Susceptibility test result',
        'transformation_logic': 'Standardized to S/I/R/NA via standardize_ast_value() function. NA = Not Tested (M2)',
        'introduced_in_stage': 1
    },
    {
        'table_name': 'stp_canonical_long',
        'column_name': 'dataset_version',
        'origin': 'metadata',
        'description': 'Dataset semantic version',
        'transformation_logic': 'Generated/assigned during ingestion (e.g., v1.0.0)',
        'introduced_in_stage': 1
    },
    
    # stp_raw_wide
    {
        'table_name': 'stp_raw_wide',
        'column_name': 'antibiotic_results',
        'origin': 'derived',
        'description': 'JSONB object of all antibiotic results',
        'transformation_logic': 'Aggregated from wide Excel columns into single JSONB field',
        'introduced_in_stage': 1
    },
]


def populate_column_provenance(dataset_version: str = "v1.0.0"):
    """
    M7: Populate column provenance registry.
    
    Documents:
    - Which columns are raw (from Excel)
    - Which are derived (extracted/computed)
    - Which are normalized (mapped to canonical values)
    - Which are metadata (system-generated)
    """
    logger.info("=" * 60)
    logger.info("STP STAGE 1: COLUMN PROVENANCE POPULATOR (M7)")
    logger.info("=" * 60)
    
    session = SessionLocal()
    
    try:
        # Clear existing provenance for this version
        session.execute(
            text("DELETE FROM stp_column_provenance WHERE dataset_version = :v"),
            {"v": dataset_version}
        )
        session.commit()
        
        logger.info(f"Populating column provenance for {dataset_version}...")
        
        # Insert provenance records
        for prov in COLUMN_PROVENANCE:
            session.execute(
                text("""
                    INSERT INTO stp_column_provenance (
                        table_name, column_name, origin, description,
                        transformation_logic, introduced_in_stage, dataset_version
                    ) VALUES (
                        :table_name, :column_name, :origin, :description,
                        :transformation_logic, :introduced_in_stage, :dataset_version
                    )
                """),
                {
                    **prov,
                    'dataset_version': dataset_version
                }
            )
            logger.info(f"  ✓ {prov['table_name']}.{prov['column_name']} [{prov['origin']}]")
        
        session.commit()
        
        # Summary by origin type
        summary = session.execute(
            text("""
                SELECT origin, COUNT(*) as count
                FROM stp_column_provenance
                WHERE dataset_version = :v
                GROUP BY origin
                ORDER BY count DESC
            """),
            {"v": dataset_version}
        ).fetchall()
        
        logger.info("-" * 60)
        logger.info(f"✓ COLUMN PROVENANCE COMPLETE (M7)")
        logger.info(f"  Total columns documented: {len(COLUMN_PROVENANCE)}")
        logger.info("\n  Breakdown by origin:")
        for row in summary:
            logger.info(f"    {row[0]}: {row[1]} columns")
        logger.info("-" * 60)
        
        return {
            "status": "success",
            "columns_documented": len(COLUMN_PROVENANCE),
            "dataset_version": dataset_version
        }
    
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Column provenance failed: {e}")
        raise
    
    finally:
        session.close()


if __name__ == "__main__":
    result = populate_column_provenance(dataset_version="v1.0.0")
    print(f"\nResult: {result}")
