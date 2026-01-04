import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import re

# Supabase Connection String
DATABASE_URL = "postgresql://postgres.zdhvyhijuriggezelyxq:Yohan%26pasi80253327@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres?sslmode=require"

EXCEL_PATH = r'd:\Yohan\Project\api\MRSA_Synthetic_PreAST_Training_12000.xlsx'

def normalize_sample_type(val):
    if not isinstance(val, str): return "Other"
    v = val.lower()
    if "blood" in v: return "Blood"
    if "urine" in v: return "Urine"
    if "pus" in v or "wound" in v or "swab" in v: return "Pus/Wound"
    if "sputum" in v: return "Sputum"
    return "Other"

def normalize_gram(val):
    if not isinstance(val, str): return "Unknown"
    v = val.lower().strip()
    if v in ["gpc", "gpcc", "gram positive cocci", "g+"]:
        return "GPC"
    return "Unknown"

def normalize_growth_time(val):
    try:
        return float(val)
    except:
        return None

def normalize_cell_count(val):
    # Map ordinal: <10->0, +->1, ++->2, +++->3, >25->4/Plenty->4
    if not isinstance(val, str): return 0
    v = val.lower().strip()
    if "<10" in v or "scanty" in v: return 0
    if "+++" in v or "plenty" in v or "many" in v: return 3 # Map massive to 3 or 4
    if "++" in v: return 2
    if "+" in v: return 1
    if ">25" in v: return 4
    return 0

def normalize_ward(val):
    if not isinstance(val, str): return "Unknown"
    return val.strip().title()

def ingest_data():
    print("Starting MRSA Stage A Ingestion...")
    
    # 1. Load Data
    print(f"Reading {EXCEL_PATH}...")
    df = pd.read_excel(EXCEL_PATH)
    initial_count = len(df)
    
    # 2. Scope Filter
    print("Filtering for Staph. aureus...")
    df = df[
        (df['Organism_Group'] == 'Staphylococci') & 
        (df['Organism'] == 'Staphylococcus aureus')
    ].copy()
    staph_count = len(df)
    print(f"filtered: {initial_count} -> {staph_count} S. aureus records.")

    # 3. Label Creation
    df['mrsa_label'] = df['Sub Organism'].apply(lambda x: 1 if isinstance(x, str) and 'MRSA' in x else 0)
    mrsa_count = df['mrsa_label'].sum()
    print(f"Labels: {mrsa_count} MRSA, {staph_count - mrsa_count} MSSA")

    # 4. Feature Normalization
    print("Normalizing features...")
    df['age'] = pd.to_numeric(df['Age'], errors='coerce').fillna(df['Age'].median())
    df['gender'] = df['Gender'].fillna('Unknown')
    df['ward'] = df['Ward / Ward No'].apply(normalize_ward)
    df['sample_type'] = df['Sample Type'].apply(normalize_sample_type)
    df['pus_type'] = df['PUS Type'].fillna('Unknown')
    df['cell_count'] = df['Cell Count'].apply(normalize_cell_count)
    df['gram_positivity'] = df['Gram Positivity'].apply(normalize_gram)
    df['growth_time'] = df['Growth Time After'].apply(normalize_growth_time).fillna(24.0)
    
    # Audit Columns
    df['bht'] = df.get('Lab No', 'Unknown') # Using Lab No as BHT/ID proxy if BHT missing, or just Unknown
    if 'Timestamp' in df.columns:
        df['original_timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    else:
        df['original_timestamp'] = None

    # 5. Select Columns (Drop Antibiotics)
    cols_to_keep = [
        'mrsa_label', 'age', 'gender', 'ward', 'sample_type', 
        'pus_type', 'cell_count', 'gram_positivity', 'growth_time',
        'bht', 'original_timestamp'
    ]
    df_clean = df[cols_to_keep]

    # 6. Database Load
    print("Connecting to Supabase...")
    engine = create_engine(DATABASE_URL)
    
    print("Truncating existing data...")
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE mrsa_raw_clean RESTART IDENTITY;"))
        conn.commit()

    print("Inserting clean records...")
    df_clean.to_sql('mrsa_raw_clean', engine, if_exists='append', index=False)
    
    print(f"Validation: Ingested {len(df_clean)} records.")
    print("Stage A Complete.")

if __name__ == "__main__":
    ingest_data()
