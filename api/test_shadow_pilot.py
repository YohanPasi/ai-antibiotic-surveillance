import os
import sys
import json
import pandas as pd
from datetime import datetime

# Add API to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from beta_lactam_service import beta_lactam_service
from shadow_mode_logger import record_shadow_outcome, compute_weekly_report, SHADOW_LOG_PATH

# Clear previous shadow log for clean test
if os.path.exists(SHADOW_LOG_PATH):
    os.remove(SHADOW_LOG_PATH)

dataset_path = os.path.join(os.path.dirname(__file__), '..', 'Raw', 'ESBL_Training_Dataset_Final_12000rows.xlsx')
try:
    df = pd.read_excel(dataset_path).dropna(subset=['Ward', 'Sample_Type'])
    df = df.head(10) # Test on 10 rows
except Exception as e:
    print(f"Dataset load failed: {e}")
    sys.exit(1)

generation_abx = {
    "CXM": "Gen2",
    "CTX": "Gen3",
    "CAZ": "Gen3",
    "CRO": "Gen3",
    "AMC": "BL_Combo",
    "TZP": "BL_Combo"
}

print("Running Shadow Mode Validation on 10 encounters...")
for idx, row in df.iterrows():
    # 1. Day 0 Input
    patient_data = {
        "Age": row.get('Age', 50),
        "Gender": row.get('Gender', 'Male'),
        "Ward": row.get('Ward', 'ICU'),
        "Sample_Type": row.get('Sample_Type', 'Blood'),
        "Organism": row.get('Organism', 'E_coli'),
    }
    
    # Predict day-0
    vector = beta_lactam_service._prepare_features(patient_data)
    spectrum = beta_lactam_service._predict_spectrum(vector)
    
    # 2. Day-3 Real AST results
    ast_panel = {}
    for col, gen in generation_abx.items():
        ds_col = f"AB_{col}" if not col.startswith("AB_") else col
        # Some column names might not have the AB_ prefix if they are named differently, try both
        actual_col = ds_col if ds_col in df.columns else (col if col in df.columns else None)
        
        if actual_col:
            val = row[actual_col]
            if pd.notna(val):
                # Map 1 -> S, 0 -> R
                ast_panel[col] = 'S' if val == 1 else 'R'
                
    print(f"AST for Encounter {idx}: {ast_panel}")
                
    # 3. Empiric Generation Picked (Dummy: pretend clinician picked the top recommended generation)
    recs = beta_lactam_service._generate_recommendations(spectrum, "Low")
    top_gen = recs[0]["generation"] if recs else "Carbapenem"
    
    # 4. Log to shadow mode
    encounter_id = f"ENC_TEST_{idx}"
    record_shadow_outcome(
        encounter_id=encounter_id,
        empiric_generation=top_gen,
        predicted_spectrum=spectrum,
        ast_panel=ast_panel,
        generation_map=generation_abx
    )

print("\n--- Weekly Stewardship Report Generated Data ---")
report = compute_weekly_report()
print(json.dumps(report, indent=2))
