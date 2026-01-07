"""Helper function for chunked ingestion - add to stp_stage_1_ingest.py"""

def ingest_stp_data_chunk(dataset_version: str, excel_file: str, start_row: int, end_row: int) -> Dict:
    """
    Ingest a chunk of rows from Excel file.
    
    Args:
        dataset_version: Semantic version
        excel_file: Path to Excel file
        start_row: Starting row index (0-based)
        end_row: Ending row index (exclusive)
    
    Returns:
        Dictionary with chunk results
    """
    import pandas as pd
    from sqlalchemy import text
    
    session = SessionLocal()
    
    try:
        # Load only the chunk
        df_full = pd.read_excel(excel_file)
        df = df_full.iloc[start_row:end_row].copy()
        
        # Extract antibiotic columns
        antibiotic_cols = extract_antibiotic_columns(df)
        
        accepted_count = 0
        rejected_count = 0
        rejection_reasons = {}
        
        wide_batch = []
        quality_log_batch = []
        
        for idx, row in df.iterrows():
            try:
                # === VALIDATION 1: Sample Date ===
                if pd.isna(row.get('Date')) or pd.isna(row.get('Sample_Date')):
                    rejection_reasons['missing_sample_date'] = rejection_reasons.get('missing_sample_date', 0) + 1
                    quality_log_batch.append({
                        'row_index': start_row + accepted_count + rejected_count,
                        'rejection_reason': 'missing_sample_date',
                        'details': {},
                        'organism_provided': None,
                        'dataset_version': dataset_version
                    })
                    rejected_count += 1
                    continue
                
                sample_date = pd.to_datetime(row.get('Date') or row.get('Sample_Date')).date()
                
                # === VALIDATION 2: Lab_No ===
                lab_no = row.get('Lab_No') or row.get('Lab No')
                if pd.isna(lab_no):
                    rejection_reasons['missing_lab_no'] = rejection_reasons.get('missing_lab_no', 0) + 1
                    quality_log_batch.append({
                        'row_index': start_row + accepted_count + rejected_count,
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
                        'row_index': start_row + accepted_count + rejected_count,
                        'rejection_reason': 'out_of_scope_organism',
                        'details': {'organism_provided': str(raw_organism)},
                        'organism_provided': str(raw_organism),
                        'dataset_version': dataset_version
                    })
                    rejected_count += 1
                    continue
                
                # === VALIDATION 4: Ward ===
                ward = str(row.get('Ward', 'Unknown')).strip() or 'Unknown'
                
                # === VALIDATION 5: Sample Type ===
                sample_type = str(row.get('Sample_Type', 'Unknown')).strip() or 'Unknown'
                
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
                        'row_index': start_row + accepted_count + rejected_count,
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
            
            except Exception as e:
                logger.error(f"Error processing row {start_row + accepted_count + rejected_count}: {e}")
                rejected_count += 1
                continue
        
        # Insert all batches for this chunk
        if wide_batch:
            insert_wide_batch(session, wide_batch)
        if quality_log_batch:
            insert_quality_log_batch(session, quality_log_batch)
        
        session.commit()
        
        return {
            'status': 'success',
            'rows_accepted': accepted_count,
            'rows_rejected': rejected_count,
            'rejection_reasons': rejection_reasons
        }
    
    except Exception as e:
        session.rollback()
        logger.error(f"Chunk ingestion failed: {e}")
        raise
    
    finally:
        session.close()
