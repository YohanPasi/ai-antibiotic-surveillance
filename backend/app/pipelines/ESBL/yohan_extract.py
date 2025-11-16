import pandas as pd
from pathlib import Path
import os, json
from datetime import datetime

# === PATHS ===
REPO_ROOT = Path(__file__).resolve().parents[4]
DATA_ROOT = REPO_ROOT / "data"
RAW_FILE = DATA_ROOT / "raw" / "Microbiology_Solid_Training_Dataset.xlsx"
OUT_DIR = DATA_ROOT / "processed" / "yohan"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# === 1. LOAD EXCEL ===
df = pd.read_excel(RAW_FILE)
print(f"Loaded {len(df)} rows, {len(df.columns)} columns from Excel.")

# === 2. RENAME COLUMNS ===
colmap = {
    "Sample_ID": "sample_id",
    "Organism": "organism",
    "Specimen_Type": "sample_type",
    "Ward": "ward",
    "Sample_Collection_Time": "collection_time",
    "Gram_Reaction": "gram",
    # ESBL-related antibiotics
    "Cefotaxime": "cefotaxime_result",
    "Ceftriaxone": "ceftriaxone_result",
    "Ceftazidime": "ceftazidime_result",
    "Cefepime": "cefepime_result",
    "Meropenem": "meropenem_result",
    "Imipenem": "imipenem_result",
}
df = df.rename(columns=colmap)

# === 3. FILTER ORGANISMS ===
mask = df["organism"].str.contains("klebsiella|coli|enterobacter", case=False, na=False)
df_filtered = df[mask].copy()
print(f"Filtered ESBL rows: {len(df_filtered)}")

# === 4. CLEAN ===
df_filtered["collection_time"] = pd.to_datetime(df_filtered["collection_time"], errors="coerce")

# === 5. SAVE ===
csv_path = OUT_DIR / "yohan_training.csv"
parquet_path = OUT_DIR / "yohan_training.parquet"
df_filtered.to_csv(csv_path, index=False)
df_filtered.to_parquet(parquet_path, index=False)

meta = {
    "generated_at": datetime.now().isoformat(timespec="seconds"),
    "organism_filter": "Klebsiella / E. coli / Enterobacter (ESBL)",
    "columns": list(df_filtered.columns)
}
with open(OUT_DIR / "yohan_dictionary.json", "w", encoding="utf-8") as f:
    json.dump(meta, f, indent=2)

print(f"✅ Saved {len(df_filtered)} rows to {csv_path}")
