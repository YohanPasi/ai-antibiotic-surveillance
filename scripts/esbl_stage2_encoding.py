
import pandas as pd
import numpy as np
import os
import sys
import json

# Define constants
INPUT_FILE = r"Processed/ESBL_Stage1_Clean.xlsx"
OUTPUT_DIR = "Processed"

# Feature definitions
DROP_COLS = ["Lab_No", "Gram_Result"] # Sample_Date handled separately
NUMERICAL_COLS = ["Age", "Growth_Time_After"]
BINARY_COLS = ["AMP", "CXM", "CTX", "CAZ", "CRO", "CIP", "CN", "AMC", "TZP"]
CATEGORICAL_COLS = ["Gender", "Ward", "Sample_Type", "PUS_Type", "Pure_Growth", "Organism", "Cell_Count_Level"]
TARGET_COL = "ESBL_Label"

def stage2_encoding():
    print("🔵 STARTING STAGE 2: FEATURE ENCODING & SPLIT")
    
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file not found: {INPUT_FILE}")
        sys.exit(1)
        
    print(f"Loading data from {INPUT_FILE}...")
    df = pd.read_excel(INPUT_FILE)
    
    # 3. Handle PUS_Type Missing Values
    print("Handling PUS_Type missing values...")
    df['PUS_Type'] = df['PUS_Type'].fillna("NA")
    
    # 4. Sort by Time
    print("Sorting by Sample_Date...")
    if 'Sample_Date' not in df.columns:
        print("❌ Sample_Date missing! Cannot sort.")
        sys.exit(1)
        
    df['Sample_Date'] = pd.to_datetime(df['Sample_Date'])
    df = df.sort_values(by='Sample_Date').reset_index(drop=True)
    
    # Drop non-ML columns
    # We drop Sample_Date now as sorting is done
    cols_to_drop = DROP_COLS + ['Sample_Date']
    df_clean = df.drop(columns=[c for c in cols_to_drop if c in df.columns])
    
    print(f"Columns after drop: {len(df_clean.columns)}")
    
    # 5. Time-Aware Split (BEFORE Encoding)
    print("Performing Time-Aware Split (80/20)...")
    split_idx = int(len(df_clean) * 0.8)
    
    train_raw = df_clean.iloc[:split_idx].copy()
    val_raw = df_clean.iloc[split_idx:].copy()
    
    print(f"Raw Train Rows: {len(train_raw)}")
    print(f"Raw Val Rows: {len(val_raw)}")
    
    # 6/7. One-Hot Encoding (Fit on Train, Apply to Val)
    print("Applying One-Hot Encoding (Fit on Train)...")
    
    # Separate predictors and target for encoding
    X_train_raw = train_raw.drop(columns=[TARGET_COL])
    y_train = train_raw[TARGET_COL]
    
    X_val_raw = val_raw.drop(columns=[TARGET_COL])
    y_val = val_raw[TARGET_COL]
    
    # Encode Train
    # Using pd.get_dummies on categorical cols only, but logic needs to be careful 
    # to keep numericals intact.
    # pd.get_dummies encodes object/category columns by default.
    # We must ensure categorical cols are truly encoded and others left alone.
    
    # Strategy: Apply get_dummies to the whole X df, specifying columns
    X_train_encoded = pd.get_dummies(X_train_raw, columns=CATEGORICAL_COLS, drop_first=False, dtype=int)
    
    # Get the feature names from train
    train_columns = X_train_encoded.columns.tolist()
    
    # Encode Val
    X_val_encoded_raw = pd.get_dummies(X_val_raw, columns=CATEGORICAL_COLS, drop_first=False, dtype=int)
    
    print("Aligning Validation columns to Train schema...")
    # Reindex val to match train columns, fill missing with 0
    X_val_encoded = X_val_encoded_raw.reindex(columns=train_columns, fill_value=0)
    
    # Ensure all data in X is numeric
    # Coerce to float/int to be safe, though get_dummies with dtype=int helps
    X_train_encoded = X_train_encoded.apply(pd.to_numeric)
    X_val_encoded = X_val_encoded.apply(pd.to_numeric)
    
    # Extract arrays
    X_train = X_train_encoded.values
    X_val = X_val_encoded.values
    y_train_arr = y_train.values
    y_val_arr = y_val.values
    
    # 8. Save Outputs
    print("Saving Outputs...")
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    np.save(os.path.join(OUTPUT_DIR, "ESBL_Stage2_X_train.npy"), X_train)
    np.save(os.path.join(OUTPUT_DIR, "ESBL_Stage2_y_train.npy"), y_train_arr)
    np.save(os.path.join(OUTPUT_DIR, "ESBL_Stage2_X_val.npy"), X_val)
    np.save(os.path.join(OUTPUT_DIR, "ESBL_Stage2_y_val.npy"), y_val_arr)
    
    # Save feature names
    feature_names_path = os.path.join(OUTPUT_DIR, "ESBL_Stage2_feature_names.json")
    with open(feature_names_path, 'w') as f:
        json.dump(train_columns, f, indent=4)
        
    # 9. Verification Checks
    print("-" * 30)
    print("VERIFICATION CHECKS:")
    
    # Shape Checks
    print(f"X_train shape: {X_train.shape}")
    print(f"X_val shape:  {X_val.shape}")
    
    if X_train.shape[0] <= X_val.shape[0]:
        print("❌ Error: Train set size not larger than val set")
        sys.exit(1)
        
    if X_train.shape[1] != X_val.shape[1]:
        print("❌ Error: Column count mismatch")
        sys.exit(1)
        
    # Content Checks
    if np.isnan(X_train).any() or np.isnan(X_val).any():
        print("❌ Error: NaNs found in X arrays")
        sys.exit(1)
        
    unique_y = np.unique(np.concatenate([y_train_arr, y_val_arr]))
    if not set(unique_y).issubset({0, 1}):
        print(f"❌ Error: Invalid target values: {unique_y}")
        sys.exit(1)
        
    # Dtype check
    if not np.issubdtype(X_train.dtype, np.number):
        print("❌ Error: X_train is not numeric")
        sys.exit(1)
        
    # Class Distribution Log
    train_pos_pct = (y_train_arr.sum() / len(y_train_arr)) * 100
    val_pos_pct = (y_val_arr.sum() / len(y_val_arr)) * 100
    
    print(f"Train ESBL Positive %: {train_pos_pct:.2f}%")
    print(f"Val ESBL Positive %:   {val_pos_pct:.2f}%")
    
    print("-" * 30)
    print("✅ STAGE 2 COMPLETED SUCCESSFULLY")
    print(f"Features: {len(train_columns)}")
    print(f"Outputs saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    stage2_encoding()
