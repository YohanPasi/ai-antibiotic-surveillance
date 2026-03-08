import pandas as pd
import sys

try:
    df = pd.read_excel(r'C:\Users\YohanN\Desktop\Project Thenula\ai-antibiotic-surveillance\Raw\Version_1_9_Final_Clean_NoMissing.xlsx', nrows=5)
    print("Columns:", list(df.columns))
    print("\nHead:\n", df.head(1).to_dict('records')[0])
except Exception as e:
    print("Error reading Excel:", e)
