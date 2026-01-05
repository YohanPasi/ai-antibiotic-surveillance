
import pandas as pd
import json
import os
import sys

# Constants
INPUT_FILE = "Processed/ESBL_Stage1_Clean.xlsx"
OUTPUT_FILE = "Config/antibiotic_outcome_tables.json"

# Potential Antibiotic Columns (Candidates)
# We will scan the dataframe for columns that are typically antibiotics.
# Based on Stage 1 analysis, they should be binary 0 (Resistant) / 1 (Susceptible)
# OR S/R. Wait, Stage 1 Cleaned converted them to 0/1?
# Let's check Stage 1 validation: "Validate antibiotic column values strictly as binary (0 or 1)."
# So we can sum them for successes.

def generate_outcome_tables():
    print("🔵 STARTING STAGE 7: OUTCOME TABLE GENERATION")
    
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file missing: {INPUT_FILE}")
        sys.exit(1)
        
    print("Loading Stage 1 Data...")
    df = pd.read_excel(INPUT_FILE)
    
    # Identify Antibiotic Columns
    # Strategy: Exclude known non-AB columns
    non_ab_cols = [
        "Lab_No", "Sample_Date", "Age", "Gender", "Ward", "Sample_Type", "Organism", 
        "ESBL_Label", "Gram_Result", "PUS_Type", "Pure_Growth", "Cell_Count_Level",
        "Growth_Time_After_Culture_Receipt", "BHT", "Is_ESBL", "Unnamed: 0"
    ]
    
    # Also exclude the defining ones if we want, but let's keep them for completeness of evidence,
    # The recommendation engine will filter them if needed.
    # Actually, Recommendation Engine excludes them from INPUT FEATURES, but for OUTPUT recommendation?
    # Usually we don't recommend Ceftriaxone for ESBL anyway.
    
    ab_cols = [c for c in df.columns if c not in non_ab_cols and df[c].dtype in ['int64', 'float64', 'int32']]
    
    print(f"Found {len(ab_cols)} potential antibiotic columns: {ab_cols}")
    
    # Initialize Outcome Structure
    outcomes = {}
    
    count_valid = 0
    
    for ab in ab_cols:
        # Check if column is binary 0/1 (allowing for NaN if any left, though Stage 1 cleaned them? Stage 1 said "Handled missing values by dropping rows (strict approach)". So should be clean.)
        # However, let's be safe.
        
        # Verify values
        unique_vals = df[ab].dropna().unique()
        if not all(v in [0, 1] for v in unique_vals):
            print(f"⚠️ Skipping {ab}: Non-binary values found {unique_vals}")
            continue
            
        # Group by ESBL Label
        # ESBL_Label: 1 = ESBL Positive (Resistance Mechanism present), 0 = Negative
        # Antibiotic Value: 1 = Susceptible (Success), 0 = Resistant (Failure)
        
        # Calculate for ESBL Group
        esbl_subset = df[df['ESBL_Label'] == 1][ab]
        esbl_total = len(esbl_subset) # Total samples for this AB in ESBL group
        # Wait, if AB column was missing for some rows (if logic allowed), we should count only non-NaNs?
        # Stage 1 dropna logic was "missing critical values". Assuming ABs are fully populated or at least we treat specific AB existing.
        # Let's count valid entries.
        esbl_valid = esbl_subset.count()
        esbl_success = esbl_subset.sum() 
        
        # Calculate for Non-ESBL Group
        non_esbl_subset = df[df['ESBL_Label'] == 0][ab]
        non_esbl_valid = non_esbl_subset.count()
        non_esbl_success = non_esbl_subset.sum()
        
        # Store
        if esbl_valid > 0 or non_esbl_valid > 0:
            outcomes[ab] = {
                "ESBL": {
                    "success": int(esbl_success),
                    "total": int(esbl_valid)
                },
                "non_ESBL": {
                    "success": int(non_esbl_success),
                    "total": int(non_esbl_valid)
                }
            }
            count_valid += 1
            
    # Save
    print(f"Generated outcomes for {count_valid} antibiotics.")
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(outcomes, f, indent=4)
        
    print("-" * 30)
    print("✅ STAGE 7 TABLE GENERATION COMPLETE")
    print(f"Saved to: {OUTPUT_FILE}")
    print("-" * 30)

if __name__ == "__main__":
    generate_outcome_tables()
