
import pandas as pd
import os

fpath = r"Processed/ESBL_Stage1_Clean.xlsx"
print(f"Checking file: {fpath}")

if not os.path.exists(fpath):
    print("❌ FILE MISSING")
    exit(1)

try:
    df = pd.read_excel(fpath)
    print(f"✅ File loaded.")
    print(f"Row count: {len(df)}")
    print(f"Columns: {len(df.columns)}")
    print(f"Missing values (total): {df.isnull().sum().sum()}")
    print("Missing values per column:")
    print(df.isnull().sum()[df.isnull().sum() > 0])
    
    # Check for specific columns
    required = ["ESBL_Label", "Lab_No"]
    for r in required:
        if r not in df.columns:
            print(f"❌ Missing required column: {r}")
            
    # Quick sanity check on ESBL label
    if 'ESBL_Label' in df.columns:
        print(f"ESBL_Label distribution:\n{df['ESBL_Label'].value_counts()}")
        
except Exception as e:
    print(f"❌ Error reading file: {e}")
