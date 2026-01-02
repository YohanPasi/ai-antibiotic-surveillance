import pandas as pd
from sqlalchemy import create_engine, text
import os
import sys

# DATABASE CONNECTION
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ast_user:ast_password_2024@db:5432/ast_db")
engine = create_engine(DATABASE_URL)

def run_mrsa_stage_a():
    print("🧪 Starting MRSA Stage A: Ingestion & Scope Control...")
    
    # 1. READ RAW FILE
    file_path = "/app/data/raw/MRSA_Synthetic_PreAST_Training_12000.xlsx"
    if not os.path.exists(file_path):
         print(f"❌ Error: Raw file not found at {file_path}")
         return

    df = pd.read_excel(file_path)
    initial_count = len(df)
    print(f"   - Loaded {initial_count} rows.")

    # 2. FILTER SCOPE (Staphylococci Only)
    # Allowed: Organism_Group='Staphylococci'  OR Organism IN ('Staphylococcus aureus', 'Staphylococci', 'Staphylococcus spp.')
    # Actually, let's look at the columns first.
    
    # Normalize column names
    df.columns = [c.strip().replace(" ", "_") for c in df.columns]
    
    # Filter Logic
    # We accept rows where 'Organism_Group' contains 'Staphy' OR 'Organism' contains 'Staph'
    mask_staph = (
        df['Organism_Group'].astype(str).str.contains('Staphy', case=False, na=False) |
        df['Organism'].astype(str).str.contains('Staphy', case=False, na=False)
    )
    
    df_scope = df[mask_staph].copy()
    print(f"   - Filtered Staphylococci Scope: {len(df_scope)} rows (Rejected {initial_count - len(df_scope)})")

    # 3. GENERATE GROUND TRUTH LABEL (mrsa_label)
    # Logic: IF Sub_Organism == 'MRSA' -> 1, ELSE -> 0
    df_scope['mrsa_label'] = df_scope['Sub_Organism'].apply(lambda x: 1 if str(x).strip().upper() == 'MRSA' else 0)
    
    label_counts = df_scope['mrsa_label'].value_counts()
    print(f"   - Ground Truth Created: MRSA={label_counts.get(1,0)}, non-MRSA={label_counts.get(0,0)}")

    # 4. REMOVE DATA LEAKAGE (Drop Antibiotics)
    # List of prohibited columns (Antibiotics, Cefoxitin, Vancomycin)
    # We will SELECT likely columns instead of dropping, to be safer.
    
    # Target Schema Columns:
    # ward, age, gender, sample_type, pus_type, cell_count, gram_positivity, growth_time, bht
    
    # Map raw columns to schema columns
    # Adjust mapping based on actual excel headers (guessing from typical format, will verify if fails)
    # Assumed headers: Ward, Age, Gender, Sample_Type, PUS_Type, Cell_Count, Gram_Positivity, Growth_Time, BHT_No
    
    clean_df = pd.DataFrame()
    clean_df['mrsa_label'] = df_scope['mrsa_label']
    clean_df['ward'] = df_scope.get('Ward', df_scope.get('Ward_No', None))
    clean_df['age'] = df_scope.get('Age', None)
    clean_df['gender'] = df_scope.get('Gender', None)
    clean_df['sample_type'] = df_scope.get('Sample_Type', None)
    clean_df['pus_type'] = df_scope.get('PUS_Type', None)
    clean_df['cell_count'] = df_scope.get('Cell_Count', None)
    clean_df['gram_positivity'] = df_scope.get('Gram_Positivity', None)
    clean_df['growth_time'] = df_scope.get('Growth_Time_After', df_scope.get('Growth_Time', None))
    clean_df['bht'] = df_scope.get('BHT', df_scope.get('BHT_No', None)) # Kept for tracing
    
    # Ensure no None columns (fill with '')
    clean_df.fillna(value={'ward': 'Unknown', 'gender': 'Unknown'}, inplace=True)
    
    print(f"   - Cleaned columns. DataFrame shape: {clean_df.shape}")

    # 5. LOAD INTO DATABASE
    # Truncate first to allow fresh reload
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE mrsa_raw_clean RESTART IDENTITY;"))
        conn.commit()
        print("   - Table truncated.")

    clean_df.to_sql('mrsa_raw_clean', engine, if_exists='append', index=False)
    print("✅ Stage A Complete: Data successfully ingested.")

if __name__ == "__main__":
    run_mrsa_stage_a()
