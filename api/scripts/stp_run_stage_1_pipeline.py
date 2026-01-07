"""
STP Stage 1: Pipeline Orchestrator
==================================
Runs the full STP Stage 1 data pipeline:
1. Ingestion & Validation
2. Wide-to-Long Transformation
3. Antibiotic Registry Building
4. Governance Report Generation
5. Descriptive Statistics Computation
6. Column Provenance Population

Usage:
    python stp_run_stage_1_pipeline.py [--force-reload] [--version v1.0.0]
"""
import argparse
import logging
import sys
import os

# Add api to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data_processor.stp_stage_1_ingest import ingest_stp_data
from data_processor.stp_wide_to_long_transform import transform_wide_to_long
from data_processor.stp_build_antibiotic_registry import build_antibiotic_registry
from data_processor.stp_generate_governance_report import generate_governance_report
from data_processor.stp_descriptive_stats import compute_descriptive_stats
from data_processor.stp_populate_column_provenance import populate_column_provenance

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_pipeline(dataset_version="v1.0.0", force_reload=False):
    try:
        logger.info(f"🚀 STARTING STP STAGE 1 PIPELINE (Version: {dataset_version})")
        
        # 1. Ingestion
        logger.info("\n=== STEP 1: INGESTION ===")
        ingest_res = ingest_stp_data(dataset_version=dataset_version, force_reload=force_reload)
        if ingest_res.get('status') == 'skipped':
            logger.info("Ingestion skipped (dataset exists). proceeding...")
        
        # 2. Transformation
        logger.info("\n=== STEP 2: TRANSFORMATION (Wide -> Long) ===")
        transform_wide_to_long(dataset_version=dataset_version)
        
        # 3. Registry
        logger.info("\n=== STEP 3: ANTIBIOTIC REGISTRY ===")
        build_antibiotic_registry(dataset_version=dataset_version)
        
        # 4. Governance
        logger.info("\n=== STEP 4: GOVERNANCE REPORT ===")
        generate_governance_report(dataset_version=dataset_version)
        
        # 5. Stats
        logger.info("\n=== STEP 5: DESCRIPTIVE STATISTICS ===")
        compute_descriptive_stats(dataset_version=dataset_version)
        
        # 6. Provenance
        logger.info("\n=== STEP 6: COLUMN PROVENANCE ===")
        populate_column_provenance(dataset_version=dataset_version)
        
        logger.info("\n✅ PIPELINE COMPLETED SUCCESSFULLY!")
        
    except Exception as e:
        logger.error(f"\n❌ PIPELINE FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run STP Stage 1 Pipeline")
    parser.add_argument("--version", default="v1.0.0", help="Dataset version identifier")
    parser.add_argument("--force-reload", action="store_true", help="Force re-ingestion of raw data")
    
    args = parser.parse_args()
    
    run_pipeline(dataset_version=args.version, force_reload=args.force_reload)
