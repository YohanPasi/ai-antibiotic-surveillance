# backend/app/pipelines/mrsa_extract.py

import os
import re
import json
from datetime import datetime
import pandas as pd

# ========= CONFIG =========
# Master Excel you curated
MASTER_XLSX = r"E:\SLIIT\SLIIT STUDY\Y4S1\Research\AI DRIVEN RESEARCH JAYATH\ai-antibiotic-surveillance\data\raw\Microbiology_Solid_Training_Dataset.xlsx"

# Output folder for MRSA-only, processed files
OUT_DIR = r"E:\SLIIT\SLIIT STUDY\Y4S1\Research\AI DRIVEN RESEARCH JAYATH\ai-antibiotic-surveillance\data\processed\mrsa"
os.makedirs(OUT_DIR, exist_ok=True)

# Acceptable truthy variants for S/I/R & gene screens
SIR_MAP = {
    "s": "S", "susceptible": "S",
    "i": "I", "intermediate": "I",
    "r": "R", "resistant": "R"
}
POS_MAP = {"positive": True, "pos": True, "detected": True, "1": True, "true": True, "yes": True}
NEG_MAP = {"negative": False, "neg": False, "not detected": False, "0": False, "false": False, "no": False}

# Keywords to auto-detect columns (handles many naming styles)
COL_HINTS = {
    "sample_id": [r"^sample[_\s]?id$", r"^sid$", r"^lab[_\s]?id$", r"^accession"],
    "patient_id": [r"^patient[_\s]?id$", r"^pid$"],
    "organism": [r"^organism$", r"species", r"^id[_\s]?result$"],
    "sample_type": [r"sample[_\s]?type", r"specimen", r"site"],
    "ward": [r"ward", r"unit", r"icu"],
    "sex": [r"^sex$", r"gender"],
    "age": [r"^age$"],
    "collection_time": [r"collection[_\s]?(date|time)", r"^date$"],
    "gram": [r"gram", r"direct\s?gram", r"microscopy"],
    "meca": [r"\bmec[a|c]\b", r"pbp2a"],
    "oxacillin": [r"oxacillin"],
    "cefoxitin": [r"cefoxitin"],
    # Useful for dashboard columns, not for label
    "vancomycin": [r"vancomycin"],
    "linezolid": [r"linezolid"],
    "daptomycin": [r"daptomycin"],
    "clindamycin": [r"clindamycin"],
    "erythromycin": [r"erythromycin"],
    "tmpsmx": [r"(tmp|co-?trim|sulfa).*smx|trimethoprim|sulfamethoxazole|co-trimoxazole"],
    "tetracycline": [r"tetracycline|doxycycline|minocycline"]
}

# =========================


def _norm(s):
    if pd.isna(s):
        return None
    return str(s).strip()


def _sir_norm(v):
    """Normalize any S/I/R string to one of 'S','I','R' or None."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    s = str(v).strip().lower()
    return SIR_MAP.get(s, s.upper() if s in ("S", "I", "R") else None)


def _bool_from_text(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    s = str(v).strip().lower()
    if s in POS_MAP:
        return True
    if s in NEG_MAP:
        return False
    return None


def _find_col(df_cols, patterns):
    """Find first column name matching any of the regex patterns (case-insensitive)."""
    for pat in patterns:
        reg = re.compile(pat, flags=re.IGNORECASE)
        for c in df_cols:
            if reg.search(str(c)):
                return c
    return None


def _auto_map_columns(df):
    """Auto-detect key column names from the Excel headers."""
    cols = list(df.columns)
    colmap = {}
    for key, pats in COL_HINTS.items():
        colmap[key] = _find_col(cols, pats)

    # Cefoxitin/Oxacillin are critical for label
    if not colmap["organism"]:
        raise ValueError("Cannot find 'Organism' column in the Excel.")
    if not (colmap["cefoxitin"] or colmap["oxacillin"] or colmap["meca"]):
        # still allow running but warn
        print("WARNING: Neither Cefoxitin nor Oxacillin nor mecA/mecC detected — labeling may be incomplete.")
    return colmap


def _is_staph_aureus(org):
    if org is None:
        return False
    s = org.lower()
    return "staphylococcus aureus" in s or s in ("s. aureus", "staph aureus", "staph. aureus")


def _build_mrsa_label(row, cefox_col, ox_col, meca_col):
    """Label rule: 1 if cefoxitin==R OR oxacillin==R OR mecA/mecC positive; 0 if both cefoxitin & oxacillin S and mec negative."""
    cefox = _sir_norm(row[cefox_col]) if cefox_col else None
    ox = _sir_norm(row[ox_col]) if ox_col else None
    mec = _bool_from_text(row[meca_col]) if meca_col else None

    # Positive paths
    if cefox == "R" or ox == "R" or mec is True:
        return 1

    # Clear negative path
    if (cefox == "S" or cefox is None) and (ox == "S" or ox is None) and (mec in (False, None)):
        # If both missing entirely, we call it unknown later. This returns 0 now but we’ll filter unknowns below if needed.
        return 0

    # Fall-back neutral: return None to drop if too ambiguous
    return None


def extract_mrsa():
    # 1) Load master Excel
    if not os.path.exists(MASTER_XLSX):
        raise FileNotFoundError(f"Master Excel not found at: {MASTER_XLSX}")
    df = pd.read_excel(MASTER_XLSX)
    print(f"Loaded {len(df)} rows, {len(df.columns)} columns from Excel.")

    # 2) Auto-map columns
    colmap = _auto_map_columns(df)
    print("Column map detected:", json.dumps(colmap, indent=2))

    # 3) Basic cleaning/normalization of a few fields
    for c in [c for c in [colmap.get("organism"), colmap.get("ward"), colmap.get("sample_type"), colmap.get("gram")] if c]:
        df[c] = df[c].apply(_norm)

    # 4) Filter Staphylococcus aureus
    df_staph = df[df[colmap["organism"]].apply(_is_staph_aureus)].copy()
    print(f"Staphylococcus aureus rows: {len(df_staph)}")

    if df_staph.empty:
        raise ValueError("No Staphylococcus aureus rows found. Check organism naming in Excel.")

    # 5) Build MRSA label
    mrsa_labels = []
    for _, row in df_staph.iterrows():
        lab = _build_mrsa_label(
            row,
            colmap.get("cefoxitin"),
            colmap.get("oxacillin"),
            colmap.get("meca"),
        )
        mrsa_labels.append(lab)
    df_staph["mrsa_label"] = mrsa_labels

    # Drop completely unknown labels (optional)
    before = len(df_staph)
    df_staph = df_staph[df_staph["mrsa_label"].isin([0, 1])]
    after = len(df_staph)
    if after < before:
        print(f"Dropped {before - after} rows with unknown/ambiguous MRSA label.")

    # 6) Build LIGHT feature subsets
    # Light #1 (admission time): ward, sample_type, age, sex, collection_time minimal
    light1_cols = []
    for key in ("sample_id", "patient_id", "collection_time", "ward", "sample_type", "sex", "age"):
        c = colmap.get(key)
        if c:
            light1_cols.append(c)
    light1_cols = list(dict.fromkeys(light1_cols))  # dedupe
    light1_cols += [colmap["organism"]]  # keep species for reference (though normally not known at Light #1)
    light1_cols = [c for c in light1_cols if c is not None]
    df_light1 = df_staph[light1_cols + ["mrsa_label"]].copy()

    # Light #4 (species identified): add Gram + key antibiotics (for dashboards / auxiliary features)
    light4_cols = light1_cols.copy()
    if colmap.get("gram"): light4_cols.append(colmap["gram"])

    optional_abx = [k for k in ("cefoxitin", "oxacillin", "vancomycin", "linezolid", "daptomycin",
                                "clindamycin", "erythromycin", "tmpsmx", "tetracycline") if colmap.get(k)]
    for k in optional_abx:
        light4_cols.append(colmap[k])
    light4_cols = list(dict.fromkeys([c for c in light4_cols if c is not None]))

    df_light4 = df_staph[light4_cols + ["mrsa_label"]].copy()

    # 7) Save outputs
    # Canonical training table (keep most useful fields)
    keep_train = list(dict.fromkeys(light4_cols + ["mrsa_label"]))
    df_train = df_staph[keep_train].copy()

    # Rename columns to a neat, stable schema for ML (optional but recommended)
    rename_map = {}
    if colmap.get("sample_id"):     rename_map[colmap["sample_id"]] = "sample_id"
    if colmap.get("patient_id"):    rename_map[colmap["patient_id"]] = "patient_id"
    if colmap.get("collection_time"): rename_map[colmap["collection_time"]] = "collection_time"
    if colmap.get("ward"):          rename_map[colmap["ward"]] = "ward"
    if colmap.get("sample_type"):   rename_map[colmap["sample_type"]] = "sample_type"
    if colmap.get("sex"):           rename_map[colmap["sex"]] = "sex"
    if colmap.get("age"):           rename_map[colmap["age"]] = "age"
    if colmap.get("organism"):      rename_map[colmap["organism"]] = "organism"
    if colmap.get("gram"):          rename_map[colmap["gram"]] = "gram"
    if colmap.get("cefoxitin"):     rename_map[colmap["cefoxitin"]] = "cefoxitin_result"
    if colmap.get("oxacillin"):     rename_map[colmap["oxacillin"]] = "oxacillin_result"
    if colmap.get("vancomycin"):    rename_map[colmap["vancomycin"]] = "vancomycin_result"
    if colmap.get("linezolid"):     rename_map[colmap["linezolid"]] = "linezolid_result"
    if colmap.get("daptomycin"):    rename_map[colmap["daptomycin"]] = "daptomycin_result"
    if colmap.get("clindamycin"):   rename_map[colmap["clindamycin"]] = "clindamycin_result"
    if colmap.get("erythromycin"):  rename_map[colmap["erythromycin"]] = "erythromycin_result"
    if colmap.get("tmpsmx"):        rename_map[colmap["tmpsmx"]] = "tmpsmx_result"
    if colmap.get("tetracycline"):  rename_map[colmap["tetracycline"]] = "tetracycline_result"

    df_train_ren = df_train.rename(columns=rename_map)
    df_light1_ren = df_light1.rename(columns=rename_map)
    df_light4_ren = df_light4.rename(columns=rename_map)

    # Save Parquet + CSV (CSV for quick human check)
    train_parquet = os.path.join(OUT_DIR, "mrsa_training.parquet")
    train_csv     = os.path.join(OUT_DIR, "mrsa_training.csv")
    light1_parq   = os.path.join(OUT_DIR, "mrsa_features_light1.parquet")
    light1_csv    = os.path.join(OUT_DIR, "mrsa_features_light1.csv")
    light4_parq   = os.path.join(OUT_DIR, "mrsa_features_light4.parquet")
    light4_csv    = os.path.join(OUT_DIR, "mrsa_features_light4.csv")
    dict_json     = os.path.join(OUT_DIR, "mrsa_dictionary.json")

    df_train_ren.to_parquet(train_parquet, index=False)
    df_train_ren.to_csv(train_csv, index=False)
    df_light1_ren.to_parquet(light1_parq, index=False)
    df_light1_ren.to_csv(light1_csv, index=False)
    df_light4_ren.to_parquet(light4_parq, index=False)
    df_light4_ren.to_csv(light4_csv, index=False)

    # Save a small data dictionary for traceability
    data_dict = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_excel": MASTER_XLSX,
        "column_map_detected": {k: v for k, v in colmap.items()},
        "label_rule": "mrsa_label = 1 if (cefoxitin==R) OR (oxacillin==R) OR (mecA/mecC positive); else 0 if both S or missing; rows with unknown dropped."
    }
    with open(dict_json, "w", encoding="utf-8") as f:
        json.dump(data_dict, f, indent=2)

    print("✅ Saved:")
    print(f"  {train_parquet}")
    print(f"  {train_csv}")
    print(f"  {light1_parq}")
    print(f"  {light1_csv}")
    print(f"  {light4_parq}")
    print(f"  {light4_csv}")    
    print(f"  {dict_json}")


if __name__ == "__main__":
    extract_mrsa()
