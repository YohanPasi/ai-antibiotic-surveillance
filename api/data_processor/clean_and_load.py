"""
Stage A: Scope Control & Data Ingestion
STRICTLY enforces Non-Fermenter filtering rules.

Accepted organisms (mapped to canonical names):
  Pseudomonas aeruginosa  → 'Pseudomonas aeruginosa'
  Acinetobacter baumannii → 'Acinetobacter baumannii'
  Acinetobacter spp.      → 'Acinetobacter baumannii'  (common lab shorthand)
  Acinetobacter spp       → 'Acinetobacter baumannii'
  Acinetobacter calcoaceticus-baumannii complex → 'Acinetobacter baumannii'

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
# Database connection parameters
DATABASE_URL = os.getenv('DATABASE_URL')


# File path
EXCEL_FILE_PATH = '/app/data/raw/Stage_D_Expanded_10000_Final_Schema_Aligned.xlsx.xlsx'

def standardize_sir_value(value):
    """Standardize S/I/R values."""
    if pd.isna(value) or value is None:
        return None
    value_str = str(value).strip().upper()
    if value_str in ['S', 'SENSITIVE', 'SUSCEPTIBLE']: return 'S'
    if value_str in ['I', 'INTERMEDIATE']: return 'I'
    if value_str in ['R', 'RESISTANT']: return 'R'
    return None

# Canonical names used throughout the system
NF_ORGANISMS = {
    'Pseudomonas aeruginosa': 'Pseudomonas aeruginosa',
    'Acinetobacter baumannii': 'Acinetobacter baumannii',
}

def get_allowed_organism(organism, sub_organism, organism_group):
    """
    STAGE A FILTER RULE — Strict Non-Fermenter scope.

    Accepted and mapped to canonical name:
      - Pseudomonas aeruginosa (any spelling/case)
      - Acinetobacter baumannii
      - Acinetobacter spp. / Acinetobacter spp (common lab shorthand → baumannii)
      - Acinetobacter calcoaceticus-baumannii complex → baumannii
      - Any row with organism_group = 'NonFermenters' AND 'acinetobacter' in name

    All Enterobacteriaceae, Staphylococcus, Enterococcus, etc. → REJECTED.
    """
    # Build normalised string for all inputs
    sub_org_str  = str(sub_organism).strip().lower()  if pd.notna(sub_organism)  else ""
    org_str      = str(organism).strip().lower()      if pd.notna(organism)      else ""
    org_grp_str  = str(organism_group).strip().lower() if pd.notna(organism_group) else ""

    # --- Pseudomonas aeruginosa ---
    if 'pseudomonas' in sub_org_str and 'aeruginosa' in sub_org_str:
        return 'Pseudomonas aeruginosa'
    if 'pseudomonas' in org_str and 'aeruginosa' in org_str:
        return 'Pseudomonas aeruginosa'

    # --- Acinetobacter (all varieties → baumannii) ---
    # Accept: baumannii, spp., spp, calcoaceticus-baumannii complex
    if 'acinetobacter' in sub_org_str:
        return 'Acinetobacter baumannii'
    if 'acinetobacter' in org_str:
        return 'Acinetobacter baumannii'

    # --- Fall-through: NonFermenters group label (paranoid catch) ---
    if 'nonfermenter' in org_grp_str or 'non-fermenter' in org_grp_str or 'non fermenter' in org_grp_str:
        # Only remap if it's one of our two genera
        if 'pseudomonas' in sub_org_str or 'pseudomonas' in org_str:
            return 'Pseudomonas aeruginosa'
        if 'acinetobacter' in sub_org_str or 'acinetobacter' in org_str:
            return 'Acinetobacter baumannii'

    # Everything else is OUT OF SCOPE
    return None

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
        if not DATABASE_URL:
            logger.error("❌ DATABASE_URL missing")
            return False
            
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
    except Exception as e:
        logger.error(f"✗ Database Error: {e}")
        return False
    
    # Clear Table
    cursor.execute("TRUNCATE TABLE ast_raw_data RESTART IDENTITY CASCADE")
    conn.commit()
    
    accepted_count = 0
    rejected_count = 0
    batch_data = []
    
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
                    lab_no, age, gender, bht_no
                ) VALUES (
                    %s, %s, %s, 'NonFermenters', %s,
                    NULL, NULL, NULL, NULL
                )
            """
            
            # Batch Collection
            batch_data.append((
                date_val, ward_val, final_organism, Json(antibiotic_results)
            ))
            
            accepted_count += 1
            if len(batch_data) >= 100:
                 cursor.executemany(insert_query, batch_data)
                 conn.commit()
                 batch_data = []
                 logger.info(f"  Ingested {accepted_count} valid Non-Fermenters...")

        except Exception as e:
            logger.error(f"Error row {idx}: {e}")
            continue

    # Insert remaining
    if batch_data:
        cursor.executemany(insert_query, batch_data)
        conn.commit()


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
