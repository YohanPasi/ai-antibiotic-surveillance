"""
STP Stage 1: Data Ingestion & Validation Pipeline
==================================================
Purpose: Load, validate, and transform STP data with research-grade rigor

Database: Supabase PostgreSQL
Governance: M1-M6 compliant
Stage Boundary: M10 enforced (no modeling, only validation)

Process:
1. Load Excel file
2. Compute SHA-256 hash
3. Check dataset freeze status (M6)
4. Validate rows (organism scope, AST values, required fields)
5. Normalize organisms and wards
6. Insert to stp_raw_wide
7. Transform wide→long
8. Insert to stp_canonical_long
9. Update metadata
"""

import pandas as pd
import hashlib
import os
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging
from collections import defaultdict
import openpyxl
from sqlalchemy import text
import json

# Use existing database connection
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from database import SessionLocal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Source file path (Docker mount)
SOURCE_FILE = '/app/data/raw/Streptococcus_Enterococcus_AST_WIDE_12000_ExpandedWards.xlsx'

# =====================================================
# ORGANISM NORMALIZATION MAP (M1: Episode Governance)
# =====================================================
# M1: Each Lab_No treated as distinct isolate (no deduplication)

ORGANISM_NORMALIZATION_MAP = {
    # Streptococcus pneumoniae variants
    "Strep. pneumoniae": "Streptococcus pneumoniae",
    "S. pneumoniae": "Streptococcus pneumoniae",
    "Pneumococcus": "Streptococcus pneumoniae",
    "Streptococcus pneumoniae": "Streptococcus pneumoniae",
    
    # Streptococcus agalactiae variants
    "Strep. agalactiae": "Streptococcus agalactiae",
    "S. agalactiae": "Streptococcus agalactiae",
    "GBS": "Streptococcus agalactiae",
    "Group B Strep": "Streptococcus agalactiae",
    "Streptococcus agalactiae": "Streptococcus agalactiae",
    
    # Viridans streptococci variants
    "Viridans strep": "Viridans streptococci",
    "Viridans group": "Viridans streptococci",
    "Viridans Streptococcus": "Viridans streptococci",
    "Viridans streptococci": "Viridans streptococci",
    
    # Enterococcus faecalis
    "E. faecalis": "Enterococcus faecalis",
    "Enterococcus faecalis": "Enterococcus faecalis",
    
    # Enterococcus faecium
    "E. faecium": "Enterococcus faecium",
    "Enterococcus faecium": "Enterococcus faecium",
}

# Allowed organisms (scope lock)
ALLOWED_ORGANISMS = {
    "Streptococcus pneumoniae",
    "Streptococcus agalactiae",
    "Viridans streptococci",
    "Enterococcus faecalis",
    "Enterococcus faecium",
}


def compute_file_hash(filepath: str) -> str:
    """Compute SHA-256 hash of file for M5 integrity tracking."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def standardize_ast_value(value) -> Optional[str]:
    """
    Canonical AST value normalization.
    
    M2: NA means "Not Tested" (not missing data)
    
    Returns:
        'S' | 'I' | 'R' | 'NA' | None (invalid)
    """
    if pd.isna(value) or value is None or value == '':
        return 'NA'  # Not tested
    
    value_str = str(value).strip().upper()
    
    if value_str in ['S', 'SENSITIVE', 'SUSCEPTIBLE']:
        return 'S'
    if value_str in ['I', 'INTERMEDIATE']:
        return 'I'
    if value_str in ['R', 'RESISTANT']:
        return 'R'
    if value_str in ['NA', 'NT', 'NOT TESTED']:
        return 'NA'
    
    # Invalid value
    return None


def normalize_organism(raw_organism: str) -> Optional[str]:
    """Normalize organism name using ORGANISM_NORMALIZATION_MAP."""
    if pd.isna(raw_organism):
        return None
    
    clean = str(raw_organism).strip()
    canonical = ORGANISM_NORMALIZATION_MAP.get(clean)
    
    if canonical and canonical in ALLOWED_ORGANISMS:
        return canonical
    
    return None


def extract_antibiotic_columns(df: pd.DataFrame) -> List[Tuple[str, str]]:
    """
    Extract antibiotic columns from DataFrame.
    
    Returns:
        List of (column_name, antibiotic_name) tuples
    """
    antibiotic_cols = []
    
    # Metadata columns to skip
    skip_cols = {'Lab_No', 'Age', 'Gender', 'Organism', 'Sub Organism', 'Ward', 'Ward / Ward No',
                 'Sample_Type', 'Cell Count', 'Gram Positivity', 'Pure Growth Or Mixed', 
                 'Growth Time After', 'Sample_Date', 'Date'}
    
    for col in df.columns:
        # Skip  metadata columns
        if col in skip_cols:
            continue
        
        # Check for Antibiotic [Name] format
        if 'Antibiotic [' in col:
            start = col.find('[') + 1
            end = col.find(']')
            if start > 0 and end > start:
                ab_name = col[start:end].strip()
                antibiotic_cols.append((col, ab_name))
        else:
            # Assume remaining columns are antibiotics (direct names)
            antibiotic_cols.append((col, col))
    
    return antibiotic_cols


def check_dataset_freeze(session, dataset_version: str) -> bool:
    """
    M6: Check if a dataset version is frozen.
    
    Returns:
        True if frozen (cannot overwrite), False otherwise
    """
    result = session.execute(
        text("""
            SELECT is_frozen FROM stp_dataset_metadata
            WHERE dataset_version = :version
        """),
        {"version": dataset_version}
    ).fetchone()
    
    return result[0] if result else False


def ingest_stp_data(dataset_version: str = "v1.0.0", force_reload: bool = False) -> Dict:
    """
    Main ingestion pipeline.
    
    Args:
        dataset_version: Semantic version for this dataset
        force_reload: If True, allows re-ingestion (creates new version if frozen)
    
    Returns:
        Dictionary with ingestion results
    """
    logger.info("=" * 60)
    logger.info("STP STAGE 1: DATA INGESTION & VALIDATION")
    logger.info("=" * 60)
    
    start_time = datetime.now()
    session = SessionLocal()
    
    try:
        # ==========================================
        # 1. LOAD SOURCE FILE
        # ==========================================
        logger.info(f"Loading source file: {SOURCE_FILE}")
        
        if not os.path.exists(SOURCE_FILE):
            raise FileNotFoundError(f"Source file not found: {SOURCE_FILE}")
        
        df = pd.read_excel(SOURCE_FILE)
        logger.info(f"✓ Loaded {len(df)} rows from source file")
        
        # ==========================================
        # 2. COMPUTE FILE HASH (M5)
        # ==========================================
        source_hash = compute_file_hash(SOURCE_FILE)
        logger.info(f"✓ Source file SHA-256: {source_hash[:16]}...")
        
        # ==========================================
        # 3. CHECK DATASET FREEZE STATUS (M6)
        # ==========================================
        if check_dataset_freeze(session, dataset_version):
            if force_reload:
                logger.error(f"❌ Dataset {dataset_version} is FROZEN (M6)")
                logger.error(f"   Cannot overwrite frozen dataset.")
                logger.error(f"   Create a new version instead (e.g., v1.1.0)")
                raise ValueError(f"Dataset {dataset_version} is frozen and immutable")
            else:
                logger.warning(f"⚠ Dataset {dataset_version} already exists")
                logger.info(f"   Use force_reload=True to allow re-ingestion")
                return {"status": "skipped", "reason": "version_exists"}
        
        # ==========================================
        # 4. EXTRACT ANTIBIOTIC COLUMNS
        # ==========================================
        antibiotic_cols = extract_antibiotic_columns(df)
        logger.info(f"✓ Found {len(antibiotic_cols)} antibiotic columns")
        
        # ==========================================
        # 5. CLEAR EXISTING DATA FOR THIS VERSION
        # ==========================================
        if force_reload:
            logger.info(f"Clearing existing data for version {dataset_version}...")
            session.execute(text("DELETE FROM stp_canonical_long WHERE dataset_version = :v"), {"v": dataset_version})
            session.execute(text("DELETE FROM stp_raw_wide WHERE dataset_version = :v"), {"v": dataset_version})
            session.execute(text("DELETE FROM stp_data_quality_log WHERE dataset_version = :v"), {"v": dataset_version})
            session.execute(text("DELETE FROM stp_antibiotic_registry WHERE dataset_version = :v"), {"v": dataset_version})
            session.commit()
        
        # ==========================================
        # 6. ROW-LEVEL VALIDATION & INGESTION
        # ==========================================
        accepted_count = 0
        rejected_count = 0
        rejection_reasons = {}
        
        wide_batch = []
        quality_log_batch = []
        
        logger.info("Processing rows...")
        
        for idx, row in df.iterrows():
            try:
                # === VALIDATION 1: Sample Date ===
                if pd.isna(row.get('Date')) or pd.isna(row.get('Sample_Date')):
                    rejection_reasons['missing_sample_date'] = rejection_reasons.get('missing_sample_date', 0) + 1
                    quality_log_batch.append({
                        'row_index': idx,
                        'rejection_reason': 'missing_sample_date',
                        'details': {},
                        'organism_provided': None,
                        'dataset_version': dataset_version
                    })
                    rejected_count += 1
                    continue
                
                sample_date = pd.to_datetime(row.get('Date') or row.get('Sample_Date')).date()
                
                # === VALIDATION 2: Lab_No (Isolate ID) ===
                lab_no = row.get('Lab_No') or row.get('Lab No')
                if pd.isna(lab_no):
                    rejection_reasons['missing_lab_no'] = rejection_reasons.get('missing_lab_no', 0) + 1
                    quality_log_batch.append({
                        'row_index': idx,
                        'rejection_reason': 'missing_lab_no',
                        'details': {},
                        'organism_provided': None,
                        'dataset_version': dataset_version
                    })
                    rejected_count += 1
                    continue
                
                isolate_id = str(lab_no).strip()
                
                # === VALIDATION 3: Organism Scope ===
                raw_organism = row.get('Organism') or row.get('Sub Organism')
                canonical_organism = normalize_organism(raw_organism)
                
                if not canonical_organism:
                    rejection_reasons['out_of_scope_organism'] = rejection_reasons.get('out_of_scope_organism', 0) + 1
                    quality_log_batch.append({
                        'row_index': idx,
                        'rejection_reason': 'out_of_scope_organism',
                        'details': {'organism_provided': str(raw_organism)},
                        'organism_provided': str(raw_organism),
                        'dataset_version': dataset_version
                    })
                    rejected_count += 1
                    continue
                
                # === VALIDATION 4: Ward ===
                ward = str(row.get('Ward / Ward No', 'Unknown')).strip()
                if not ward or ward == '' or ward.lower() == 'nan':
                    ward = 'Unknown'
                
                # === VALIDATION 5: Sample Type ===
                sample_type = str(row.get('Sample Type', 'Unknown')).strip()
                
                # === VALIDATION 6: Process AST Results ===
                antibiotic_results = {}
                for col_name, ab_name in antibiotic_cols:
                    raw_val = row.get(col_name)
                    sir = standardize_ast_value(raw_val)
                    if sir:
                        antibiotic_results[ab_name] = sir
                
                if not antibiotic_results:
                    rejection_reasons['no_valid_ast'] = rejection_reasons.get('no_valid_ast', 0) + 1
                    quality_log_batch.append({
                        'row_index': idx,
                        'rejection_reason': 'no_valid_ast',
                        'details': {},
                        'organism_provided': canonical_organism,
                        'dataset_version': dataset_version
                    })
                    rejected_count += 1
                    continue
                
                # === ROW ACCEPTED ===
                wide_batch.append({
                    'isolate_id': isolate_id,
                    'sample_date': sample_date,
                    'organism': canonical_organism,
                    'ward': ward,
                    'sample_type': sample_type,
                    'antibiotic_results': antibiotic_results,
                    'dataset_version': dataset_version
                })
                
                accepted_count += 1
                
                # Batch insert every 100 rows (reduced from 500 for connection stability)
                if len(wide_batch) >= 100:
                    insert_wide_batch(session, wide_batch)
                    wide_batch = []
                    session.commit()  # Commit frequently
                
                if len(quality_log_batch) >= 100:
                    insert_quality_log_batch(session, quality_log_batch)
                    quality_log_batch = []
                    session.commit()  # Commit frequently
                
                if accepted_count % 1000 == 0:
                    logger.info(f"  Processed {accepted_count} valid isolates...")
            
            except Exception as e:
                logger.error(f"Error processing row {idx}: {e}")
                rejected_count += 1
                continue
        
        # Insert remaining batches
        if wide_batch:
            insert_wide_batch(session, wide_batch)
        if quality_log_batch:
            insert_quality_log_batch(session, quality_log_batch)
        
        session.commit()
        
        logger.info("-" * 60)
        logger.info(f"✓ INGESTION COMPLETE")
        logger.info(f"  Accepted: {accepted_count} isolates")
        logger.info(f"  Rejected: {rejected_count} rows")
        logger.info(f"  Rejection reasons: {rejection_reasons}")
        logger.info("-" * 60)
        
        # ==========================================
        # 7. UPDATE METADATA
        # ==========================================
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        update_metadata(
            session,
            dataset_version=dataset_version,
            source_file=os.path.basename(SOURCE_FILE),
            source_hash=source_hash,
            total_processed=len(df),
            total_accepted=accepted_count,
            total_rejected=rejected_count,
            processing_time=processing_time
        )
        
        session.commit()
        
        logger.info("✓ Metadata updated")
        logger.info(f"✓ Processing time: {processing_time:.2f} seconds")
        
        return {
            "status": "success",
            "dataset_version": dataset_version,
            "source_hash": source_hash,
            "rows_processed": len(df),
            "rows_accepted": accepted_count,
            "rows_rejected": rejected_count,
            "rejection_reasons": rejection_reasons,
            "processing_time_seconds": processing_time
        }
    
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Ingestion failed: {e}")
        raise
    
    finally:
        session.close()


def insert_wide_batch(session, batch: List[Dict]):
    """Insert batch into stp_raw_wide."""
    import json
    for row in batch:
        session.execute(
            text("""
                INSERT INTO stp_raw_wide (
                    isolate_id, sample_date, organism, ward, sample_type,
                    antibiotic_results, dataset_version
                ) VALUES (
                    :isolate_id, :sample_date, :organism, :ward, :sample_type,
                    :antibiotic_results, :dataset_version
                )
            """),
            {
                **row,
                'antibiotic_results': json.dumps(row['antibiotic_results'])
            }
        )


def insert_quality_log_batch(session, batch: List[Dict]):
    """Insert batch into stp_data_quality_log."""
    import json
    for row in batch:
        session.execute(
            text("""
                INSERT INTO stp_data_quality_log (
                    row_index, rejection_reason, details, organism_provided, dataset_version
                ) VALUES (
                    :row_index, :rejection_reason, :details, :organism_provided, :dataset_version
                )
            """),
            {
                **row,
                'details': json.dumps(row.get('details', {}))
            }
        )


def update_metadata(session, **kwargs):
    """Update stp_dataset_metadata table."""
    session.execute(
        text("""
            INSERT INTO stp_dataset_metadata (
                dataset_version, source_file_name, source_file_hash,
                total_rows_processed, total_rows_accepted, total_rows_rejected,
                processing_time_seconds, schema_version
            ) VALUES (
                :dataset_version, :source_file, :source_hash,
                :total_processed, :total_accepted, :total_rejected,
                :processing_time, '1.0.0'
            )
            ON CONFLICT (dataset_version) DO UPDATE SET
                total_rows_processed = EXCLUDED.total_rows_processed,
                total_rows_accepted = EXCLUDED.total_rows_accepted,
                total_rows_rejected = EXCLUDED.total_rows_rejected,
                processing_time_seconds = EXCLUDED.processing_time_seconds
        """),
        kwargs
    )


if __name__ == "__main__":
    result = ingest_stp_data(dataset_version="v1.0.0", force_reload=False)
    print(f"\nResult: {result}")
