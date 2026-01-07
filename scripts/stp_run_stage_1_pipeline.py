"""
STP Stage 1: Pipeline Orchestrator
===================================
Purpose: One-command execution of complete Stage 1 pipeline

Usage:
    python scripts/stp_run_stage_1_pipeline.py --version v1.0.0

Database: Supabase PostgreSQL (via DATABASE_URL)
"""

import sys
import os
import argparse
import logging
from datetime import datetime

# Add api directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

from database import SessionLocal, test_connection
from data_processor.stp_stage_1_ingest import ingest_stp_data
from data_processor.stp_wide_to_long_transform import transform_wide_to_long
from data_processor.stp_build_antibiotic_registry import build_antibiotic_registry
from data_processor.stp_generate_governance_report import generate_governance_report
from data_processor.stp_descriptive_stats import compute_descriptive_stats
from data_processor.stp_populate_column_provenance import populate_column_provenance

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_complete_pipeline(dataset_version: str, force_reload: bool = False):
    """
    Execute complete STP Stage 1 pipeline.
    
    Steps:
    1. Ingest & validate (M6 freeze check)
    2. Transform wide→long
    3. Build antibiotic registry
    4. Generate governance report (M1-M10, O1-O2)
    5. Compute descriptive stats (M3)
    6. Populate column provenance (M7)
    
    Args:
        dataset_version: Semantic version (e.g., v1.0.0)
        force_reload: Allow overwrite if not frozen
    """
    logger.info("=" * 70)
    logger.info("STP STAGE 1: COMPLETE PIPELINE ORCHESTRATOR")
    logger.info("=" * 70)
    logger.info(f"Dataset Version: {dataset_version}")
    logger.info(f"Force Reload: {force_reload}")
    logger.info(f"Database: Supabase (via DATABASE_URL)")
    logger.info("=" * 70)
    
    start_time = datetime.now()
    
    try:
        # Step 1: Ingest
        logger.info("\n[1/6] INGESTING & VALIDATING DATA...")
        logger.info("-" * 70)
        ingest_result = ingest_stp_data(
            dataset_version=dataset_version,
            force_reload=force_reload
        )
        
        if ingest_result.get('status') == 'skipped':
            logger.warning("⚠️  Ingestion skipped - dataset already exists")
            logger.info("   Use --force to reload")
            return
        
        logger.info(f"✓ Ingested {ingest_result['rows_accepted']:,} isolates")
        logger.info(f"✓ Rejected {ingest_result['rows_rejected']:,} rows")
        
        # Step 2: Transform
        logger.info("\n[2/6] TRANSFORMING WIDE → LONG...")
        logger.info("-" * 70)
        transform_result = transform_wide_to_long(dataset_version=dataset_version)
        logger.info(f"✓ Created {transform_result['ast_tests']:,} AST test records")
        
        # Step 3: Antibiotic Registry
        logger.info("\n[3/6] BUILDING ANTIBIOTIC REGISTRY...")
        logger.info("-" * 70)
        registry_result = build_antibiotic_registry(dataset_version=dataset_version)
        logger.info(f"✓ Tracked {registry_result['antibiotics_tracked']} antibiotics")
        
        # Step 4: Governance Report
        logger.info("\n[4/6] GENERATING GOVERNANCE REPORT (M1-M10, O1-O2)...")
        logger.info("-" * 70)
        governance_result = generate_governance_report(dataset_version=dataset_version)
        logger.info(f"✓ Generated {governance_result['declarations_count']} declarations")
        logger.info(f"✓ Markdown: {governance_result.get('markdown_file', 'N/A')}")
        
        # Step 5: Descriptive Statistics
        logger.info("\n[5/6] COMPUTING DESCRIPTIVE STATISTICS (M3)...")
        logger.info("-" * 70)
        stats_result = compute_descriptive_stats(dataset_version=dataset_version)
        stats = stats_result['stats']
        logger.info(f"✓ Total isolates: {stats['total_isolates']:,}")
        logger.info(f"✓ Total AST tests: {stats['total_ast_tests']:,}")
        logger.info(f"✓ Organisms: {len(stats['organism_distribution'])}")
        logger.info(f"✓ M3 Sparse months: {stats['sparse_month_count']}")
        
        # Step 6: Column Provenance
        logger.info("\n[6/6] POPULATING COLUMN PROVENANCE (M7)...")
        logger.info("-" * 70)
        provenance_result = populate_column_provenance(dataset_version=dataset_version)
        logger.info(f"✓ Documented {provenance_result['columns_documented']} columns")
        
        # Summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ PIPELINE COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Dataset Version: {dataset_version}")
        logger.info(f"Total Time: {duration:.1f} seconds")
        logger.info(f"Isolates: {ingest_result['rows_accepted']:,}")
        logger.info(f"AST Tests: {transform_result['ast_tests']:,}")
        logger.info(f"Antibiotics: {registry_result['antibiotics_tracked']}")
        logger.info(f"Governance: M1-M10 + O1-O2 Complete")
        logger.info("=" * 70)
        logger.info("\n📋 Next Steps:")
        logger.info("  1. Review governance report")
        logger.info("  2. Review descriptive statistics")
        logger.info("  3. Run tests: pytest tests/test_stp_stage_1.py")
        logger.info("  4. Freeze dataset: python scripts/stp_freeze_dataset.py")
        logger.info("=" * 70)
        
        return {
            'status': 'success',
            'dataset_version': dataset_version,
            'duration_seconds': duration,
            'isolates': ingest_result['rows_accepted'],
            'ast_tests': transform_result['ast_tests']
        }
    
    except Exception as e:
        logger.error("=" * 70)
        logger.error(f"❌ PIPELINE FAILED: {e}")
        logger.error("=" * 70)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='STP Stage 1: Complete Pipeline Orchestrator'
    )
    parser.add_argument(
        '--version',
        type=str,
        default='v1.0.0',
        help='Dataset version (default: v1.0.0)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force reload even if version exists'
    )
    
    args = parser.parse_args()
    
    # Test database connection
    if not test_connection():
        logger.error("❌ Database connection failed")
        logger.error("   Check DATABASE_URL environment variable")
        sys.exit(1)
    
    run_complete_pipeline(
        dataset_version=args.version,
        force_reload=args.force
    )
