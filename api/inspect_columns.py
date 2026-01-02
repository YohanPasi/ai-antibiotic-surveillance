import pandas as pd

SOURCE_FILE = "/app/data/raw/Version_1_9_Final_Clean_NoMissing.xlsx"

try:
    df = pd.read_excel(SOURCE_FILE)
    print("Columns found:")
    for col in df.columns:
        print(f" - {col}")
except Exception as e:
    print(f"Error: {e}")
