"""
STP Stage 1: Chunked Pipeline Runner
=====================================
Processes Excel file in 1000-row chunks to avoid Supabase pooler timeouts
"""
import sys
sys.path.insert(0, '/app')

from database import SessionLocal
from data_processor.stp_stage_1_ingest import (
    extract_antibiotic_columns, normalize_organism, standardize_ast_value,
    insert_wide_batch, insert_quality_log_batch
)
from data_processor.stp_wide_to_long_transform import transform_wide_to_long
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ingest_chunk(dataset_version, df_chunk, antibiotic_cols, chunk_start):
    """Process a chunk of rows."""
    session = SessionLocal()
    
    try:
        accepted_count = 0
        rejected_count = 0
        
        wide_batch = []
        quality_log_batch = []
        
        for local_idx, row in df_chunk.iterrows():
            global_idx = chunk_start + (local_idx - df_chunk.index[0])
            
            try:
                # Validation 1: Sample Date
                if pd.isna(row.get('Date')) and pd.isna(row.get('Sample_Date')):
                    quality_log_batch.append({
                        'row_index': global_idx,
                        'rejection_reason': 'missing_sample_date',
                        'details': {},
                        'organism_provided': None,
                        'dataset_version': dataset_version
                    })
                    rejected_count += 1
                    continue
                
                sample_date = pd.to_datetime(row.get('Date') or row.get('Sample_Date')).date()
                
                # Validation 2: Lab_No
                lab_no = row.get('Lab_No') or row.get('Lab No')
                if pd.isna(lab_no):
                    quality_log_batch.append({
                        'row_index': global_idx,
                        'rejection_reason': 'missing_lab_no',
                        'details': {},
                        'organism_provided': None,
                        'dataset_version': dataset_version
                    })
                    rejected_count += 1
                    continue
                
                isolate_id = str(lab_no).strip()
                
                # Validation 3: Organism
                raw_organism = row.get('Organism') or row.get('Sub Organism')
                canonical_organism = normalize_organism(raw_organism)
                
                if not canonical_organism:
                    quality_log_batch.append({
                        'row_index': global_idx,
                        'rejection_reason': 'out_of_scope_organism',
                        'details': {'organism_provided': str(raw_organism)},
                        'organism_provided': str(raw_organism),
                        'dataset_version': dataset_version
                    })
                    rejected_count += 1
                    continue
                
                ward = str(row.get('Ward', 'Unknown')).strip() or 'Unknown'
                sample_type = str(row.get('Sample_Type', 'Unknown')).strip() or 'Unknown'
                
                # Process AST
                antibiotic_results = {}
                for col_name, ab_name in antibiotic_cols:
                    raw_val = row.get(col_name)
                    sir = standardize_ast_value(raw_val)
                    if sir:
                        antibiotic_results[ab_name] = sir
                
                if not antibiotic_results:
                    quality_log_batch.append({
                        'row_index': global_idx,
                        'rejection_reason': 'no_valid_ast',
                        'details': {},
                        'organism_provided': canonical_organism,
                        'dataset_version': dataset_version
                    })
                    rejected_count += 1
                    continue
                
                # Accept row
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
            
            except Exception as e:
                logger.error(f"Error at row {global_idx}: {e}")
                rejected_count += 1
        
        # Insert batches
        if wide_batch:
            insert_wide_batch(session, wide_batch)
        if quality_log_batch:
            insert_quality_log_batch(session, quality_log_batch)
        
        session.commit()
        return accepted_count, rejected_count
    
    finally:
        session.close()


print("=" * 70)
print("STP STAGE 1: CHUNKED PROCESSING")
print("=" * 70)

dataset_version = 'v1.0.0'
excel_file = '/app/data/raw/Streptococcus_Enterococcus_AST_WIDE_12000_ExpandedWards.xlsx'
chunk_size = 1000

# Load file
df = pd.read_excel(excel_file)
total_rows = len(df)
antibiotic_cols = extract_antibiotic_columns(df)

print(f"Total rows: {total_rows}")
print(f"Antibiotics: {len(antibiotic_cols)}")
print(f"Chunk size: {chunk_size}")
print()

total_accepted = 0
total_rejected = 0

for chunk_start in range(0, total_rows, chunk_size):
    chunk_end = min(chunk_start + chunk_size, total_rows)
    chunk_num = (chunk_start // chunk_size) + 1
    
    logger.info(f"[Chunk {chunk_num}] Rows {chunk_start}-{chunk_end-1}")
    
    df_chunk = df.iloc[chunk_start:chunk_end]
    accepted, rejected = ingest_chunk(dataset_version, df_chunk, antibiotic_cols, chunk_start)
    
    total_accepted += accepted
    total_rejected += rejected
    logger.info(f"  ✓ Accepted: {accepted}, Rejected: {rejected}")

print("\n" + "=" * 70)
print("✅ INGESTION COMPLETE")
print(f"Total accepted: {total_accepted}")
print(f"Total rejected: {total_rejected}")

# Transform
logger.info("\nRunning transformation...")
result = transform_wide_to_long(dataset_version=dataset_version)
logger.info(f"✓ Created {result['ast_tests']} AST tests")
print("\n✅ DONE!")
