"""
Stage A: Scope Control & Data Ingestion
STRICTLY enforces Non-Fermenter filtering rules.
Allowed: 'Pseudomonas aeruginosa', 'Acinetobacter baumannii'
Restricted: Patient Identifiers, Demographics.
"""
import pandas as pd
import psycopg2
from psycopg2.extras import Json
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection parameters
DB_PARAMS = {
    'host': os.getenv('DB_HOST', 'db'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'ast_db'),
    'user': os.getenv('DB_USER', 'ast_user'),
    'password': os.getenv('DB_PASSWORD', 'ast_password_2024')
}

# File path
EXCEL_FILE_PATH = '/app/data/raw/Version_1_9_Final_Clean_NoMissing.xlsx'

def standardize_sir_value(value):
    """Standardize S/I/R values."""
    if pd.isna(value) or value is None:
        return None
    value_str = str(value).strip().upper()
    if value_str in ['S', 'SENSITIVE', 'SUSCEPTIBLE']: return 'S'
    if value_str in ['I', 'INTERMEDIATE']: return 'I'
    if value_str in ['R', 'RESISTANT']: return 'R'
    return None

def get_allowed_organism(organism, sub_organism, organism_group):
    """
    STAGE A FILTER RULE:
    Accept ONLY: 'Pseudomonas aeruginosa', 'Acinetobacter baumannii'
    Reject ALL others.
    """
    # 1. Check Organism Group Scope
    # Note: Sometimes Group is missing, so we double check the name.
    # But if Group is explicit "Enterobacteriaceae", we should probably drop it.
    # The requirement says: KEEP rows where Organism_Group == "NonFermenters"
    
    org_grp_str = str(organism_group).strip().lower() if pd.notna(organism_group) else ""
    
    # 2. Check Specific Sub-Organisms
    sub_org_str = str(sub_organism).strip().lower() if pd.notna(sub_organism) else ""
    
    # Normalization Logic
    final_organism = None
    
    if 'pseudomonas' in sub_org_str and 'aeruginosa' in sub_org_str:
        final_organism = 'Pseudomonas aeruginosa'
    elif 'acinetobacter' in sub_org_str and 'baumannii' in sub_org_str:
        final_organism = 'Acinetobacter baumannii'
    
    # If not found by name, check if strictly labeled NonFermenter group and try to map?
    # Requirement says: "Normalize sub-organism to ONLY PsA or Ab. Anything else -> DROP"
    # So if it's "Acinetobacter spp", strictly speaking, Stage A should DROP it if the rule is strict.
    # The user said: "Acinetobacter baumannii". "Anything else -> DROP".
    # So "Acinetobacter spp" is DROPPED.
    
    return final_organism

def extract_antibiotic_columns(df):
    """Extract antibiotic columns."""
    antibiotic_cols = []
    for col in df.columns:
        if 'Antibiotic [' in col:
            start = col.find('[') + 1
            end = col.find(']')
            if start > 0 and end > start:
                ab_name = col[start:end].strip()
                antibiotic_cols.append((col, ab_name))
    return antibiotic_cols

def clean_and_load_data():
    logger.info("="*60)
    logger.info("⚡ STAGE A: INGESTION & SCOPE CONTROL")
    logger.info("="*60)
    
    try:
        df = pd.read_excel(EXCEL_FILE_PATH)
        logger.info(f"✓ Raw Dataset: {len(df)} rows")
    except Exception as e:
        logger.error(f"✗ Load Error: {e}")
        return False

    antibiotic_cols = extract_antibiotic_columns(df)
    
    # Connect
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
    except Exception as e:
        logger.error(f"✗ Database Error: {e}")
        return False
    
    # Clear Table
    cursor.execute("TRUNCATE TABLE ast_raw_data RESTART IDENTITY CASCADE")
    conn.commit()
    
    accepted_count = 0
    rejected_count = 0
    
    for idx, row in df.iterrows():
        try:
            # 1. SCOPE FILTER
            final_organism = get_allowed_organism(
                row.get('Organism'),
                row.get('Sub Organism'),
                row.get('Organism_Group')
            )
            
            if not final_organism:
                rejected_count += 1
                continue # DROP
                
            # 2. COLUMN SELECTION (Whitelist)
            # Allowed: Date, Ward, Sub_Organism (Mapped), Antibiotic, AST Result
            # Excluded: Age, Gender, Lab No, BHT, etc.
            
            # Extract Allowed Keys
            date_val = pd.to_datetime(row['Date']).date() if pd.notna(row.get('Date')) else None
            ward_val = str(row.get('Ward / Ward No', '')).strip() if pd.notna(row.get('Ward / Ward No')) else None
            
            # Process AST Results
            antibiotic_results = {}
            for col_name, ab_name in antibiotic_cols:
                raw_val = row.get(col_name)
                sir = standardize_sir_value(raw_val)
                if sir:
                    antibiotic_results[ab_name] = sir
            
            if not antibiotic_results:
                rejected_count += 1
                continue # Drop empty AST
                
            # INSERT (Privacy Preserving - No PII)
            # Note: ast_raw_data table schema might have extra columns. 
            # We will insert NULLs into them to enforce privacy.
            
            insert_query = """
                INSERT INTO ast_raw_data (
                    date, ward, sub_organism, organism_group, antibiotic_results,
                    
                    -- Explicitly NULL out restricted PII columns even if DB has them
                    lab_no, age, gender, bht_no
                ) VALUES (
                    %s, %s, %s, 'NonFermenters', %s,
                    NULL, NULL, NULL, NULL
                )
            """
            
            cursor.execute(insert_query, (
                date_val, ward_val, final_organism, Json(antibiotic_results)
            ))
            
            accepted_count += 1
            if accepted_count % 100 == 0:
                logger.info(f"  Ingested {accepted_count} valid Non-Fermenters...")
                
        except Exception as e:
            logger.error(f"Error row {idx}: {e}")
            continue

    conn.commit()
    cursor.close()
    conn.close()
    
    logger.info("-" * 40)
    logger.info(f"✓ SCOPE ENFORCEMENT COMPLETE")
    logger.info(f"  Accepted Rows (Non-Fermenters): {accepted_count}")
    logger.info(f"  Rejected Rows (Out of Scope):   {rejected_count}")
    logger.info("-" * 40)
    return True

if __name__ == "__main__":
    clean_and_load_data()
