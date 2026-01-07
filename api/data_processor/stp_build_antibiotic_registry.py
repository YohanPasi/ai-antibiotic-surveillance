"""
STP Stage 1: Antibiotic Registry Builder
=========================================
Purpose: Data-driven antibiotic coverage tracking

Demonstrates:
- No cherry-picking of antibiotics
- 100% data-driven
- Coverage transparency

Publication Impact: Prevents accusations of selective reporting
"""

import logging
from sqlalchemy import text
import os
from datetime import datetime
import sys

# Use existing database connection
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from database import SessionLocal

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def build_antibiotic_registry(dataset_version: str = "v1.0.0"):
    """
    Build data-driven antibiotic registry.
    
    Process:
    1. Query all antibiotics from stp_canonical_long
    2. Calculate test counts and coverage
    3. Store in stp_antibiotic_registry
    
    Critical: This list is NEVER manually edited - 100% data-driven
    """
    logger.info("=" * 60)
    logger.info("STP STAGE 1: ANTIBIOTIC REGISTRY BUILDER")
    logger.info("=" * 60)
    
    session = SessionLocal()
    
    try:
        # Clear existing registry for this version
        session.execute(
            text("DELETE FROM stp_antibiotic_registry WHERE dataset_version = :v"),
            {"v": dataset_version}
        )
        session.commit()
        
        # Get total isolates
        total_isolates = session.execute(
            text("""
                SELECT COUNT(DISTINCT isolate_id)
                FROM stp_canonical_long
                WHERE dataset_version = :v
            """),
            {"v": dataset_version}
        ).scalar()
        
        logger.info(f"Total isolates: {total_isolates}")
        
        # Calculate antibiotic coverage
        logger.info("Calculating antibiotic coverage...")
        
        results = session.execute(
            text("""
                SELECT 
                    antibiotic,
                    COUNT(*) as test_count,
                    COUNT(DISTINCT isolate_id) as isolates_tested,
                    MIN(sample_date) as first_seen,
                    MAX(sample_date) as last_seen
                FROM stp_canonical_long
                WHERE dataset_version = :v
                AND ast_result != 'NA'  -- Only count actual tests, not "Not Tested"
                GROUP BY antibiotic
                ORDER BY test_count DESC
            """),
            {"v": dataset_version}
        ).fetchall()
        
        # Insert into registry
        for row in results:
            antibiotic = row[0]
            test_count = row[1]
            isolates_tested = row[2]
            first_seen = row[3]
            last_seen = row[4]
            coverage_percent = (isolates_tested / total_isolates * 100) if total_isolates > 0 else 0
            
            session.execute(
                text("""
                    INSERT INTO stp_antibiotic_registry (
                        antibiotic_name, test_count, coverage_percent,
                        first_seen, last_seen, dataset_version
                    ) VALUES (
                        :antibiotic, :test_count, :coverage_percent,
                        :first_seen, :last_seen, :dataset_version
                    )
                """),
                {
                    'antibiotic': antibiotic,
                    'test_count': test_count,
                    'coverage_percent': round(coverage_percent, 2),
                    'first_seen': first_seen,
                    'last_seen': last_seen,
                    'dataset_version': dataset_version
                }
            )
        
        session.commit()
        
        logger.info("-" * 60)
        logger.info(f"✓ ANTIBIOTIC REGISTRY COMPLETE")
        logger.info(f"  Antibiotics tracked: {len(results)}")
        logger.info(f"  Total isolates: {total_isolates}")
        
        # Show top 10
        logger.info("\nTop 10 antibiotics by coverage:")
        for i, row in enumerate(results[:10], 1):
            coverage = (row[2] / total_isolates * 100) if total_isolates > 0 else 0
            logger.info(f"  {i}. {row[0]}: {row[2]:,} isolates ({coverage:.1f}%)")
        
        logger.info("-" * 60)
        
        return {
            "status": "success",
            "antibiotics_tracked": len(results),
            "total_isolates": total_isolates,
            "dataset_version": dataset_version
        }
    
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Registry build failed: {e}")
        raise
    
    finally:
        session.close()


if __name__ == "__main__":
    result = build_antibiotic_registry(dataset_version="v1.0.0")
    print(f"\nResult: {result}")
