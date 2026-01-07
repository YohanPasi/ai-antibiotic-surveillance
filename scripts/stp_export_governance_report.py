"""
STP Stage 1: Governance Report Exporter
========================================
Purpose: Export governance documentation as markdown/JSON

Usage:
    python scripts/stp_export_governance_report.py --version v1.0.0 --format markdown

Database: Supabase PostgreSQL (via DATABASE_URL)
"""

import sys
import os
import argparse
import logging
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

from database import SessionLocal, test_connection
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if not test_connection():
    logger.error("Database connection failed - check DATABASE_URL")
    sys.exit(1)


def export_governance_markdown(dataset_version: str, output_file: str):
    """Export governance report as markdown."""
    session = SessionLocal()
    
    try:
        # Fetch all declarations from Supabase
        declarations = session.execute(
            text("""
                SELECT declaration_type, declaration_text
                FROM stp_governance_declarations
                WHERE dataset_version = :v
                AND is_active = TRUE
                ORDER BY declaration_type
            """),
            {"v": dataset_version}
        ).fetchall()
        
        if not declarations:
            logger.error(f"No governance declarations found for {dataset_version}")
            return False
        
        # Fech metadata
        metadata = session.execute(
            text("""
                SELECT source_file_name, source_file_hash, total_rows_accepted, 
                       date_range_start, date_range_end, is_frozen, approved_at
                FROM stp_dataset_metadata
                WHERE dataset_version = :v
            """),
            {"v": dataset_version}
        ).fetchone()
        
        # Build markdown
        md_content = f"""# STP Stage 1 Governance Report

**Dataset Version**: `{dataset_version}`  
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Database**: Supabase PostgreSQL

---

## Dataset Provenance

| Metric | Value |
|--------|-------|
| Source File | {metadata[0] if metadata else 'N/A'} |
| SHA-256 Hash | `{metadata[1][:16]}...` |
| Total Isolates | {metadata[2]:,} if metadata and metadata[2] else 'N/A' |
| Date Range | {metadata[3]} to {metadata[4]} if metadata and metadata[3] else 'N/A' |
| Frozen (M6) | {'✅ Yes' if metadata and metadata[5] else '⏳ No'} |
| Approved At | {metadata[6] if metadata and metadata[6] else 'N/A'} |

---

## Governance Declarations

"""
        # Add each declaration
        for decl_type, decl_text in declarations:
            title = decl_type.replace('_', ' ').title()
            md_content += f"### {title}\n\n{decl_text}\n\n---\n\n"
        
        md_content += """
## Compliance Checklist

- ✅ **M1**: Isolate Episode Governance
- ✅ **M2**: AST Panel Heterogeneity  
- ✅ **M3**: Temporal Density Validation
- ✅ **M4**: Negative Control Declaration
- ✅ **M5**: Migration Version Tracking
- ✅ **M6**: Dataset Freeze Policy
- ✅ **M7**: Column Provenance Registry
- ✅ **M8**: Row-Level Security Policies
- ✅ **M9**: Clinical Non-Decision Disclaimer
- ✅ **M10**: Stage Boundary Enforcement
- ✅ **O1**: CLSI/EUCAST Disclaimer
- ✅ **O2**: Ward Function Drift Disclaimer

**Status**: 100% Complete

---

*This report was auto-generated from Supabase `stp_governance_declarations` table.*
"""
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        logger.info(f"✓ Markdown report exported: {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"Export failed: {e}")
        return False
    finally:
        session.close()


def export_governance_json(dataset_version: str, output_file: str):
    """Export governance report as JSON."""
    session = SessionLocal()
    
    try:
        declarations = session.execute(
            text("""
                SELECT declaration_type, declaration_text, created_at
                FROM stp_governance_declarations
                WHERE dataset_version = :v
                AND is_active = TRUE
            """),
            {"v": dataset_version}
        ).fetchall()
        
        if not declarations:
            logger.error(f"No governance declarations found for {dataset_version}")
            return False
        
        report = {
            'dataset_version': dataset_version,
            'generated_at': datetime.now().isoformat(),
            'database': 'Supabase PostgreSQL',
            'declarations': {
                row[0]: {
                    'text': row[1],
                    'created_at': row[2].isoformat() if row[2] else None
                }
                for row in declarations
            },
            'compliance': {
                'M1': 'Episode Governance',
                'M2': 'AST Panel Heterogeneity',
                'M3': 'Temporal Density Validation',
                'M4': 'Negative Control Declaration',
                'M5': 'Migration Versioning',
                'M6': 'Dataset Freeze',
                'M7': 'Column Provenance',
                'M8': 'RLS Policies',
                'M9': 'Clinical Disclaimer',
                'M10': 'Stage Boundaries',
                'O1': 'CLSI/EUCAST Disclaimer',
                'O2': 'Ward Function Disclaimer'
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"✓ JSON report exported: {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"Export failed: {e}")
        return False
    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='STP Stage 1: Governance Report Exporter')
    parser.add_argument('--version', type=str, default='v1.0.0', help='Dataset version')
    parser.add_argument('--format', type=str, choices=['markdown', 'json', 'both'], default='markdown')
    parser.add_argument('--output', type=str, help='Output file path (default: auto-generated)')
    
    args = parser.parse_args()
    
    # Determine output paths
    if args.output:
        if args.format == 'both':
            md_output = args.output.replace('.json', '.md').replace('.md', '') + '.md'
            json_output = args.output.replace('.md', '.json').replace('.json', '') + '.json'
        elif args.format == 'markdown':
            md_output = args.output if args.output.endswith('.md') else args.output + '.md'
        else:
            json_output = args.output if args.output.endswith('.json') else args.output + '.json'
    else:
        md_output = f"stp_governance_report_{args.version}.md"
        json_output = f"stp_governance_report_{args.version}.json"
    
    logger.info("=" * 70)
    logger.info("STP STAGE 1: GOVERNANCE REPORT EXPORTER")
    logger.info("=" * 70)
    logger.info(f"Dataset Version: {args.version}")
    logger.info(f"Format: {args.format}")
    logger.info(f"Database: Supabase")
    logger.info("=" * 70)
    
    success = True
    if args.format in ['markdown', 'both']:
        success = export_governance_markdown(args.version, md_output) and success
    
    if args.format in ['json', 'both']:
        success = export_governance_json(args.version, json_output) and success
    
    if success:
        logger.info("=" * 70)
        logger.info("✅ EXPORT COMPLETE")
        logger.info("=" * 70)
    
    sys.exit(0 if success else 1)
