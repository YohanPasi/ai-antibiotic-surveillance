import os
import re
import json
from datetime import datetime
import pandas as pd

# ========= CONFIG =========
MASTER_XLSX = r"E:\SLIIT\SLIIT STUDY\Y4S1\Research\AI DRIVEN RESEARCH JAYATH\ai-antibiotic-surveillance\data\raw\Microbiology_Solid_Training_Dataset.xlsx"

OUT_DIR = r"E:\SLIIT\SLIIT STUDY\Y4S1\Research\AI DRIVEN RESEARCH JAYATH\ai-antibiotic-surveillance\data\processed\nonfermenter"
os.makedirs(OUT_DIR, exist_ok=True)

SIR_MAP = {
    "s": "S", "susceptible": "S",
    "i": "I", "intermediate": "I",
    "r": "R", "resistant": "R"
}

POS_MAP = {"positive": True, "pos": True, "detected": True, "1": True, "true": True, "yes": True}
NEG_MAP = {"negative": False, "neg": False, "not detected": False, "0": False, "false": False, "no": False}

# IMPORTANT: Antibiotics for non-fermenters (Pseudomonas + Acinetobacter)
COL_HINTS = {
    "sample_id": [r"sample[_\s]?id", r"sid", r"accession"],
    "patient_id": [r"patient[_\s]?id", r"pid"],
    "organism": [r"organism", r"species"],
    "sample_type": [r"specimen", r"sample[_\s]?type"],
    "ward": [r"ward", r"unit", r"icu"],
    "sex": [r"sex", r"gender"],
    "age": [r"age"],
    "collection_time": [r"collection", r"date"],
    "gram": [r"gram"],

    # Key antibiotics (available in your dataset):
    "meropenem": [r"mero", r"meropenem"],
    "imipenem": [r"imi", r"imipenem"],
    "ceftazidime": [r"ceftazidime"],
    "cefepime": [r"cefepime"],
    "amikacin": [r"amikacin"],
    "gentamicin": [r"gentamicin"],
    "tobramycin": [r"tobramycin"],
    "ciprofloxacin": [r"cipro", r"ciprofloxacin"],
    "colistin": [r"colistin", r"polymyxin"],
}


def _norm(x):
    if pd.isna(x): return None
    return str(x).strip()


def _sir_norm(x):
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    s = str(x).strip().lower()
    if s in SIR_MAP: return SIR_MAP[s]
    if s.upper() in ("S", "I", "R"): return s.upper()
    return None


def _find_col(columns, patterns):
    for pat in patterns:
        reg = re.compile(pat, re.IGNORECASE)
        for c in columns:
            if reg.search(str(c)):
                return c
    return None


def _auto_map_columns(df):
    colmap = {}
    for key, hints in COL_HINTS.items():
        colmap[key] = _find_col(df.columns, hints)
    return colmap


def _is_nonfermenter(org):
    if not org: return False
    text = org.lower().strip()
    return (
        "pseudomonas aeruginosa" in text or
        "p. aeruginosa" in text or
        "acinetobacter baumannii" in text or
        "a. baumannii" in text
    )


def _carbapenem_label(row, mero_col, imi_col):
    mero = _sir_norm(row[mero_col]) if mero_col else None
    imi = _sir_norm(row[imi_col]) if imi_col else None

    if mero == "R" or imi == "R":
        return 1  # Carbapenem Resistant

    if mero == "S" and imi == "S":
        return 0

    return None  # unknown → dropped


def extract_nonfermenters():
    if not os.path.exists(MASTER_XLSX):
        raise FileNotFoundError(MASTER_XLSX)

    df = pd.read_excel(MASTER_XLSX)
    print(f"Loaded {len(df)} rows from Excel.")

    colmap = _auto_map_columns(df)
    print("Column mapping:", json.dumps(colmap, indent=2))

    org_col = colmap["organism"]
    df[org_col] = df[org_col].apply(_norm)

    df_nf = df[df[org_col].apply(_is_nonfermenter)].copy()
    print(f"Non-fermenter isolates found: {len(df_nf)}")

    if df_nf.empty:
        raise ValueError("No non-fermenter organisms found! Check Excel column names.")

    mero_col = colmap["meropenem"]
    imi_col = colmap["imipenem"]

    labels = []
    for _, row in df_nf.iterrows():
        labels.append(_carbapenem_label(row, mero_col, imi_col))

    df_nf["carbapenem_resistant"] = labels

    before = len(df_nf)
    df_nf = df_nf[df_nf["carbapenem_resistant"].isin([0, 1])]
    print("Dropped ambiguous rows:", before - len(df_nf))

    keep_cols = [
        colmap["sample_id"], colmap["patient_id"], colmap["sample_type"],
        colmap["ward"], colmap["age"], colmap["sex"], colmap["collection_time"],
        colmap["organism"], colmap["gram"],
        colmap["meropenem"], colmap["imipenem"],
        colmap["ceftazidime"], colmap["cefepime"],
        colmap["amikacin"], colmap["gentamicin"], colmap["tobramycin"],
        colmap["ciprofloxacin"], colmap["colistin"],
        "carbapenem_resistant"
    ]
    keep_cols = [c for c in keep_cols if c]

    df_clean = df_nf[keep_cols].copy()

    rename_map = {
        colmap["sample_id"]: "sample_id",
        colmap["patient_id"]: "patient_id",
        colmap["sample_type"]: "sample_type",
        colmap["ward"]: "ward",
        colmap["age"]: "age",
        colmap["sex"]: "sex",
        colmap["collection_time"]: "collection_time",
        colmap["organism"]: "organism",
        colmap["gram"]: "gram",
        colmap["meropenem"]: "meropenem",
        colmap["imipenem"]: "imipenem",
        colmap["ceftazidime"]: "ceftazidime",
        colmap["cefepime"]: "cefepime",
        colmap["amikacin"]: "amikacin",
        colmap["gentamicin"]: "gentamicin",
        colmap["tobramycin"]: "tobramycin",
        colmap["ciprofloxacin"]: "ciprofloxacin",
        colmap["colistin"]: "colistin",
    }

    df_clean = df_clean.rename(columns=rename_map)

    csv_path = os.path.join(OUT_DIR, "nonfermenter_clean.csv")
    parq_path = os.path.join(OUT_DIR, "nonfermenter_clean.parquet")
    dict_path = os.path.join(OUT_DIR, "nonfermenter_dictionary.json")

    df_clean.to_csv(csv_path, index=False)
    df_clean.to_parquet(parq_path, index=False)

    metadata = {
        "generated_at": datetime.now().isoformat(),
        "rows": len(df_clean),
        "columns": list(df_clean.columns),
        "label_definition": "1 = Carbapenem-resistant (Meropenem R or Imipenem R)",
        "source": MASTER_XLSX
    }
    with open(dict_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print("Saved:")
    print(" -", csv_path)
    print(" -", parq_path)
    print(" -", dict_path)


if __name__ == "__main__":
    extract_nonfermenters()
