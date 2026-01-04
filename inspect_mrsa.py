import pandas as pd
import os

file_path = r'd:\Yohan\Project\api\MRSA_Synthetic_PreAST_Training_12000.xlsx'
if os.path.exists(file_path):
    df = pd.read_excel(file_path, nrows=5)
    print("Columns:", df.columns.tolist())
    print("\nSample Data:\n", df.head(2))
else:
    print(f"File not found: {file_path}")
