
import pandas as pd
import os
import sys

# Define constants
INPUT_FILE = r"Raw/ESBL_Training_Dataset_Final_12000rows.xlsx"
OUTPUT_DIR = "Processed"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "ESBL_Stage1_Clean.xlsx")

REQUIRED_COLUMNS = [
    "Lab_No", "Sample_Date", "Age", "Gender", "Ward", "Sample_Type", "PUS_Type",
    "Pure_Growth", "Growth_Time_After", "Organism", "Gram_Result", "Cell_Count_Level",
    "AMP", "CXM", "CTX", "CAZ", "CRO", "CIP", "CN", "AMC", "TZP", "ESBL_Label"
]

ANTIBIOTIC_COLS = ["AMP", "CXM", "CTX", "CAZ", "CRO", "CIP", "CN", "AMC", "TZP", "ESBL_Label"]

ALLOWED_ORGANISMS = ["E_coli", "Klebsiella_pneumoniae", "Enterobacter_spp"]

def validate_and_clean_dataset():
    print("🔵 STARTING STAGE 1: DATASET PREPARATION & VALIDATION")
    
    # 1. Load Data
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file not found: {INPUT_FILE}")
        sys.exit(1)
        
    print(f"Loading data from {INPUT_FILE}...")
    try:
        df = pd.read_excel(INPUT_FILE)
    except Exception as e:
        print(f"❌ Failed to read Excel file: {e}")
        sys.exit(1)

    initial_count = len(df)
    print(f"Initial row count: {initial_count}")
    
    # 2. Structure Validation
    # Row count 
    if len(df) < 10000:
        print(f"❌ Validation Failed: Dataset has {len(df)} rows, expected >= 10,000")
        sys.exit(1)
        
    # Column presence
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        print(f"❌ Validation Failed: Missing columns: {missing_cols}")
        sys.exit(1)
        
    print("✅ Structure validation passed.")

    # 3. Cohort Validation (Enterobacterales only)
    print("Running Cohort Validation...")
    df = df[df['Organism'].isin(ALLOWED_ORGANISMS)]
    print(f"Rows after Organism filter: {len(df)} (Dropped: {initial_count - len(df)})")

    # 4. Gram Stain Consistency
    print("Running Gram Stain Consistency Check...")
    prev_count = len(df)
    df = df[df['Gram_Result'] == 'GNB']
    print(f"Rows after Gram_Result filter: {len(df)} (Dropped: {prev_count - len(df)})")

    # 5. Antibiotic Value Validation (Binary 0/1)
    print("Running Antibiotic Value Validation...")
    prev_count = len(df)
    
    # Convert to numeric, forcing errors to NaN, then checking for non-binary
    # First, ensure no strings/garbage
    for col in ANTIBIOTIC_COLS:
        # Coerce to numeric
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    # Keep only rows where all ATB cols are valid 0 or 1
    # Check for NaN first (failed conversion)
    df = df.dropna(subset=ANTIBIOTIC_COLS)
    
    # Check for values that remain that are not 0 or 1
    condition = pd.Series(True, index=df.index)
    for col in ANTIBIOTIC_COLS:
        condition = condition & (df[col].isin([0, 1]))
    
    df = df[condition]
    print(f"Rows after Antibiotic Value filter: {len(df)} (Dropped: {prev_count - len(df)})")

    # 6. ESBL Label Sanity Check
    print("Running ESBL Label Sanity Check...")
    prev_count = len(df)
    
    # Logic: 
    # ESBL=1 -> (CTX=1 OR CAZ=1 OR CRO=1)
    # ESBL=0 -> (CTX=0 AND CAZ=0 AND CRO=0)
    
    # We can assume 0/1 values now
    
    def is_consistent_esbl(row):
        is_esbl = row['ESBL_Label'] == 1
        has_phenotype = (row['CTX'] == 1) or (row['CAZ'] == 1) or (row['CRO'] == 1)
        
        if is_esbl:
            return has_phenotype # Must have phenotype
        else:
            return not has_phenotype # Must NOT have phenotype
            
    df = df[df.apply(is_consistent_esbl, axis=1)]
    print(f"Rows after ESBL Label sanity check: {len(df)} (Dropped: {prev_count - len(df)})")

    # 7. Age & Growth Time Validation
    print("Running Age & Growth Time Validation...")
    prev_count = len(df)
    
    # Age: 0 < Age <= 100
    df = df[(df['Age'] > 0) & (df['Age'] <= 100)]
    
    # Growth Time: 6 <= Time <= 72
    df = df[(df['Growth_Time_After'] >= 6) & (df['Growth_Time_After'] <= 72)]
    
    print(f"Rows after Age/Growth filter: {len(df)} (Dropped: {prev_count - len(df)})")

    # 8. Missing Value Handling
    print("Running Missing Value Handling...")
    prev_count = len(df)
    
    CRITICAL_COLS = ["Organism", "Ward", "Sample_Type"] + ANTIBIOTIC_COLS
    df = df.dropna(subset=CRITICAL_COLS)
    
    print(f"Rows after Missing Value filter: {len(df)} (Dropped: {prev_count - len(df)})")

    # 9. Duplicate Handling
    print("Running Duplicate Handling...")
    prev_count = len(df)
    
    # Drop duplicate Lab_No, keep first
    df = df.drop_duplicates(subset=['Lab_No'], keep='first')
    
    print(f"Rows after Duplicate filter: {len(df)} (Dropped: {prev_count - len(df)})")

    # 10. Column Cleanup
    print("Running Column Cleanup...")
    # Keep only required columns that are not PII
    # User listed removal of: Patient_ID, BHT, free text, Final diagnosis, Carbapenem
    # Our REQUIRED_COLUMNS list seems safe, but let's double check it doesn't have forbidden ones.
    # It has Lab_No which is needed for ID but is pseudo-anonymized usually.
    # It does NOT have Patient_ID or BHT.
    
    final_cols = [c for c in REQUIRED_COLUMNS if c in df.columns]
    df = df[final_cols]
    
    # 11. Output
    print("Saving Clean Dataset...")
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    df.to_excel(OUTPUT_FILE, index=False)
    
    print("-" * 30)
    print(f"✅ STAGE 1 COMPLETED SUCCESSFULLY")
    print(f"Final Row Count: {len(df)}")
    if len(df) < 10000:
         print("⚠️ WARNING: Final row count is below 10,000!")
    print(f"Output Saved: {OUTPUT_FILE}")
    print("-" * 30)

if __name__ == "__main__":
    validate_and_clean_dataset()
