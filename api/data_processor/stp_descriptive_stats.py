"""
STP Stage 1: Descriptive Statistics Generator
==============================================
Purpose: Publication-ready descriptive statistics (Table 1 material)

Includes:
- Sample size statistics
- M3: Temporal density validation (sparse period flagging)
- Organism/ward/sample type distributions
- Antibiotic coverage
- Missingness rates

M10 Firewall: NO resistance rates, trends, or statistical tests
"""

import logging
from sqlalchemy import text
import os
import json
from datetime import datetime
from collections import defaultdict
import sys

# Use existing database connection
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from database import SessionLocal

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# M3: Sparse period threshold
SPARSE_THRESHOLD_ISOLATES_PER_MONTH = 20


def compute_descriptive_stats(dataset_version: str = "v1.0.0") -> dict:
    """
    Generate complete descriptive statistics.
    
    M3: Includes temporal density validation
    M10: NO modeling - only counts and distributions
    """
    logger.info("=" * 60)
    logger.info("STP STAGE 1: DESCRIPTIVE STATISTICS")
    logger.info("=" * 60)
    
    session = SessionLocal()
    
    try:
        stats = {}
        
        # 1. SAMPLE SIZE
        logger.info("Computing sample sizes...")
        stats['total_isolates'] = session.execute(
            text("""
                SELECT COUNT(DISTINCT isolate_id)
                FROM stp_canonical_long
                WHERE dataset_version = :v
            """),
            {"v": dataset_version}
        ).scalar()
        
        stats['total_ast_tests'] = session.execute(
            text("""
                SELECT COUNT(*)
                FROM stp_canonical_long
                WHERE dataset_version = :v
            """),
            {"v": dataset_version}
        ).scalar()
        
        logger.info(f"  Total isolates: {stats['total_isolates']:,}")
        logger.info(f"  Total AST tests: {stats['total_ast_tests']:,}")
        
        # 2. ORGANISM DISTRIBUTION
        logger.info("Computing organism distribution...")
        organism_dist = session.execute(
            text("""
                SELECT 
                    organism,
                    COUNT(DISTINCT isolate_id) as count,
                    ROUND(COUNT(DISTINCT isolate_id) * 100.0 / :total, 2) as percentage
                FROM stp_canonical_long
                WHERE dataset_version = :v
                GROUP BY organism
                ORDER BY count DESC
            """),
            {"v": dataset_version, "total": stats['total_isolates']}
        ).fetchall()
        
        stats['organism_distribution'] = [
            {
                'organism': row[0],
                'count': row[1],
                'percentage': float(row[2])
            }
            for row in organism_dist
        ]
        
        # 3. WARD DISTRIBUTION
        logger.info("Computing ward distribution...")
        ward_dist = session.execute(
            text("""
                SELECT 
                    ward,
                    COUNT(DISTINCT isolate_id) as count,
                    ROUND(COUNT(DISTINCT isolate_id) * 100.0 / :total, 2) as percentage
                FROM stp_canonical_long
                WHERE dataset_version = :v
                GROUP BY ward
                ORDER BY count DESC
            """),
            {"v": dataset_version, "total": stats['total_isolates']}
        ).fetchall()
        
        stats['ward_distribution'] = [
            {
                'ward': row[0],
                'count': row[1],
                'percentage': float(row[2])
            }
            for row in ward_dist
        ]
        
        # 4. SAMPLE TYPE DISTRIBUTION
        logger.info("Computing sample type distribution...")
        sample_dist = session.execute(
            text("""
                SELECT 
                    sample_type,
                    COUNT(DISTINCT isolate_id) as count,
                    ROUND(COUNT(DISTINCT isolate_id) * 100.0 / :total, 2) as percentage
                FROM stp_canonical_long
                WHERE dataset_version = :v
                GROUP BY sample_type
                ORDER BY count DESC
            """),
            {"v": dataset_version, "total": stats['total_isolates']}
        ).fetchall()
        
        stats['sample_type_distribution'] = [
            {
                'sample_type': row[0] if row[0] else 'Unknown',
                'count': row[1],
                'percentage': float(row[2])
            }
            for row in sample_dist
        ]
        
        # 5. M3: TEMPORAL DENSITY VALIDATION
        logger.info("Computing temporal density (M3)...")
        monthly_counts = session.execute(
            text("""
                SELECT 
                    DATE_TRUNC('month', sample_date)::date as month,
                    COUNT(DISTINCT isolate_id) as isolate_count
                FROM stp_canonical_long
                WHERE dataset_version = :v
                GROUP BY DATE_TRUNC('month', sample_date)
                ORDER BY month
            """),
            {"v": dataset_version}
        ).fetchall()
        
        sparse_months = []
        temporal_density = []
        
        for row in monthly_counts:
            month = row[0]
            count = row[1]
            is_sparse = count < SPARSE_THRESHOLD_ISOLATES_PER_MONTH
            
            temporal_density.append({
                'month': month.strftime('%Y-%m') if month else 'Unknown',
                'isolate_count': count,
                'density_flag': 'SPARSE' if is_sparse else 'ADEQUATE'
            })
            
            if is_sparse:
                sparse_months.append(month.strftime('%Y-%m') if month else 'Unknown')
        
        stats['temporal_density'] = temporal_density
        stats['sparse_months'] = sparse_months
        stats['sparse_month_count'] = len(sparse_months)
        
        logger.info(f"  Total months: {len(temporal_density)}")
        logger.info(f"  Sparse months (<{SPARSE_THRESHOLD_ISOLATES_PER_MONTH} isolates): {len(sparse_months)}")
        
        # 6. ANTIBIOTIC COVERAGE
        logger.info("Computing antibiotic coverage...")
        ab_coverage = session.execute(
            text("""
                SELECT 
                    antibiotic,
                    COUNT(DISTINCT isolate_id) as isolates_tested,
                    COUNT(*) as total_tests,
                    ROUND(COUNT(DISTINCT isolate_id) * 100.0 / :total, 2) as coverage_percent
                FROM stp_canonical_long
                WHERE dataset_version = :v
                AND ast_result != 'NA'
                GROUP BY antibiotic
                ORDER BY isolates_tested DESC
            """),
            {"v": dataset_version, "total": stats['total_isolates']}
        ).fetchall()
        
        stats['antibiotic_coverage'] = [
            {
                'antibiotic': row[0],
                'isolates_tested': row[1],
                'total_tests': row[2],
                'coverage_percent': float(row[3])
            }
            for row in ab_coverage
        ]
        
        # 7. MISSINGNESS ANALYSIS
        logger.info("Computing missingness rates...")
        
        # Get antibiotic count per isolate
        isolate_coverage = session.execute(
            text("""
                SELECT isolate_id, COUNT(*) as antibiotics_tested
                FROM stp_canonical_long
                WHERE dataset_version = :v
                AND ast_result != 'NA'
                GROUP BY isolate_id
            """),
            {"v": dataset_version}
        ).fetchall()
        
        total_antibiotics = len(ab_coverage)
        coverage_bins = {
            '100%': 0,
            '75-99%': 0,
            '50-74%': 0,
            '<50%': 0
        }
        
        for row in isolate_coverage:
            tested = row[1]
            coverage = (tested / total_antibiotics * 100) if total_antibiotics > 0 else 0
            
            if coverage == 100:
                coverage_bins['100%'] += 1
            elif coverage >= 75:
                coverage_bins['75-99%'] += 1
            elif coverage >= 50:
                coverage_bins['50-74%'] += 1
            else:
                coverage_bins['<50%'] += 1
        
        stats['missingness_summary'] = {
            'total_antibiotics_available': total_antibiotics,
            'coverage_bins': coverage_bins
        }
        
        # 8. DATE RANGE
        date_range = session.execute(
            text("""
                SELECT 
                    MIN(sample_date) as earliest,
                    MAX(sample_date) as latest
                FROM stp_canonical_long
                WHERE dataset_version = :v
            """),
            {"v": dataset_version}
        ).fetchone()
        
        stats['date_range'] = {
            'earliest': date_range[0].strftime('%Y-%m-%d') if date_range[0] else None,
            'latest': date_range[1].strftime('%Y-%m-%d') if date_range[1] else None
        }
        
        logger.info("-" * 60)
        logger.info(f"✓ DESCRIPTIVE STATISTICS COMPLETE")
        logger.info(f"  Organisms: {len(stats['organism_distribution'])}")
        logger.info(f"  Wards: {len(stats['ward_distribution'])}")
        logger.info(f"  Antibiotics: {len(stats['antibiotic_coverage'])}")
        logger.info(f"  M3 Sparse months: {stats['sparse_month_count']}")
        logger.info("-" * 60)
        
        # Save to JSON file
        output_path = save_stats_to_file(stats, dataset_version)
        
        return {
            "status": "success",
            "stats": stats,
            "output_file": output_path,
            "dataset_version": dataset_version
        }
    
    except Exception as e:
        logger.error(f"❌ Descriptive stats failed: {e}")
        raise
    
    finally:
        session.close()


def save_stats_to_file(stats: dict, dataset_version: str) -> str:
    """Save statistics to JSON file."""
    output_dir = os.path.join(os.path.dirname(__file__), '../../docs')
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, f'stp_descriptive_stats_{dataset_version}.json')
    
    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2, default=str)
    
    logger.info(f"  ✓ Statistics saved: {output_path}")
    
    return output_path


if __name__ == "__main__":
    result = compute_descriptive_stats(dataset_version="v1.0.0")
    print(f"\nStats computed: {result['output_file']}")
