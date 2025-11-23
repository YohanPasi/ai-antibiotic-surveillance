import pandas as pd
import os
from pathlib import Path

# Get project root (4 levels up from this file: STREP -> pipelines -> app -> backend -> project_root)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent

# Path to your master dataset (relative to project root)
EXCEL_PATH = PROJECT_ROOT / "data" / "raw" / "Microbiology_Solid_Training_Dataset.xlsx"

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "strep"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# Streptococcus species keywords
STREP_KEYWORDS = [
    "Streptococcus", "S. pyogenes", "S. agalactiae",
    "Group A Streptococcus", "Group B Streptococcus",
    "GAS", "GBS", "Streptococcus pneumoniae", "S. pneumoniae"
]


def extract_strep():
    print("Loading Excel...")
    df = pd.read_excel(EXCEL_PATH)
    print(f"Loaded {len(df)} rows.")

    # Normalize column names
    columns = {c.lower().strip(): c for c in df.columns}

    def find(colname):
        colname = colname.lower()
        for c in df.columns:
            if colname in c.lower():
                return c
        return None

    colmap = {
        "sample_id": find("sample"),
        "patient_id": find("patient"),
        "organism": find("organism"),
        "sample_type": find("specimen"),
        "ward": find("ward"),
        "age": find("age"),
        "sex": find("sex"),
        "collection_time": find("date") or find("collection"),
    }

    # AST columns
    ast_cols = {
        "penicillin": find("penicillin"),
        "erythromycin": find("erythro"),
        "clindamycin": find("clinda"),
        "ceftriaxone": find("ceftria"),
        "vancomycin": find("vanco"),
        "linezolid": find("linez"),
    }

    print("Column mapping:")
    print(colmap)
    print(ast_cols)

    # Filter Streptococcus isolates
    df["organism_lower"] = df[colmap["organism"]].astype(str).str.lower()
    strep_df = df[df["organism_lower"].str.contains("strepto")]

    print(f"Streptococcus isolates found: {len(strep_df)}")

    # Filter out None values and get only columns that were found
    found_colmap = {k: v for k, v in colmap.items() if v is not None}
    found_ast_cols = {k: v for k, v in ast_cols.items() if v is not None}
    
    # Get list of actual column names to select
    columns_to_select = list(found_colmap.values()) + list(found_ast_cols.values())
    
    # Clean subset
    cleaned = strep_df[columns_to_select].copy()

    # Rename columns to match the keys (only for columns that were found)
    rename_map = {v: k for k, v in found_colmap.items()}
    rename_map.update({v: k for k, v in found_ast_cols.items()})
    cleaned = cleaned.rename(columns=rename_map)

    # Save cleaned files
    cleaned.to_csv(OUTPUT_DIR / "strep_clean.csv", index=False)
    cleaned.to_parquet(OUTPUT_DIR / "strep_clean.parquet")

    print("Saved:")
    print(" - strep_clean.csv")
    print(" - strep_clean.parquet")

    return cleaned


if __name__ == "__main__":
    extract_strep()
