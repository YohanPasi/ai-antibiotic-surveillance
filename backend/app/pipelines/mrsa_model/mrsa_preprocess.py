import pandas as pd
import json
import numpy as np
from pathlib import Path

# Paths
# Get project root (5 levels up from this file: mrsa_model -> pipelines -> app -> backend -> project_root)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed" / "mrsa"
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)


# File inputs (data is in processed folder, not raw)
FILE_TRAIN = DATA_PROCESSED / "mrsa_training.csv"
FILE_L1 = DATA_PROCESSED / "mrsa_features_light1.csv"
FILE_L4 = DATA_PROCESSED / "mrsa_features_light4.csv"


# Leakage columns that MUST NOT be used in ML
LEAKAGE_COLUMNS = [
    "oxacillin", "cefoxitin", "meca", "mecA", "mecA_result",
    "cefoxitin_screen", "oxacillin_screen"
]


def load_csv(path: Path):
    df = pd.read_csv(path)
    print(f"Loaded: {path.name} → shape={df.shape}")
    return df


def clean_columns(df: pd.DataFrame):
    """Standardize column names and remove leakage."""
    original_cols = df.columns.tolist()

    df = df.rename(columns=lambda c: c.strip().lower().replace(" ", "_"))

    # Drop leakage columns
    drop_cols = [c for c in df.columns if c in LEAKAGE_COLUMNS]
    if drop_cols:
        print("Dropping leakage columns:", drop_cols)
        df = df.drop(columns=drop_cols)

    return df, original_cols


def merge_training(train_df, l1_df, l4_df):
    """Merge training labels into both Light1 and Light4 feature frames."""

    # ---- find key columns in training ----
    sample_id_col = None
    for col in train_df.columns:
        if "sample" in col.lower() and "id" in col.lower():
            sample_id_col = col
            break

    if sample_id_col is None:
        print("Available columns in training data:", train_df.columns.tolist())
        raise ValueError(
            "Training dataset must contain 'sample_id' (or similar) as the key identifier."
        )

    mrsa_label_col = None
    for col in train_df.columns:
        if "mrsa" in col.lower() and "label" in col.lower():
            mrsa_label_col = col
            break

    if mrsa_label_col is None:
        print("Available columns in training data:", train_df.columns.tolist())
        raise ValueError(
            f"Training dataset missing 'mrsa_label' column. Available: {train_df.columns.tolist()}"
        )

    # ---- find sample_id columns in L1/L4 ----
    l1_sample_id = None
    for col in l1_df.columns:
        if "sample" in col.lower() and "id" in col.lower():
            l1_sample_id = col
            break

    l4_sample_id = None
    for col in l4_df.columns:
        if "sample" in col.lower() and "id" in col.lower():
            l4_sample_id = col
            break

    if l1_sample_id is None or l4_sample_id is None:
        raise ValueError(
            f"Light dataframes missing sample_id. L1: {l1_df.columns.tolist()}, L4: {l4_df.columns.tolist()}"
        )

    # ---- if Light tables already have mrsa_label, we don't really need to merge labels ----
    l1_has_label = any("mrsa" in c.lower() and "label" in c.lower() for c in l1_df.columns)
    l4_has_label = any("mrsa" in c.lower() and "label" in c.lower() for c in l4_df.columns)

    if l1_has_label and l4_has_label:
        # Just align column name to 'mrsa_label' and return
        def normalize_label(df):
            label_cols = [c for c in df.columns if "mrsa" in c.lower() and "label" in c.lower()]
            # pick first and rename to mrsa_label
            if label_cols and label_cols[0] != "mrsa_label":
                df = df.rename(columns={label_cols[0]: "mrsa_label"})
            return df

        l1 = normalize_label(l1_df.copy())
        l4 = normalize_label(l4_df.copy())

    else:
        # ---- normal path: Light tables do NOT have labels; pull from training file ----
        merge_cols = [sample_id_col, mrsa_label_col]

        l1 = l1_df.merge(
            train_df[merge_cols],
            left_on=l1_sample_id,
            right_on=sample_id_col,
            how="left",
        )
        l4 = l4_df.merge(
            train_df[merge_cols],
            left_on=l4_sample_id,
            right_on=sample_id_col,
            how="left",
        )

        # remove duplicate sample_id columns if present
        if sample_id_col != l1_sample_id and sample_id_col in l1.columns:
            l1 = l1.drop(columns=[sample_id_col])
        if sample_id_col != l4_sample_id and sample_id_col in l4.columns:
            l4 = l4.drop(columns=[sample_id_col])

        # coalesce mrsa_label_x / mrsa_label_y into mrsa_label
        def coalesce_label(df):
            cols = df.columns
            if "mrsa_label" in cols:
                return df  # already clean

            src_cols = [c for c in cols if c.startswith("mrsa_label")]
            if not src_cols:
                return df

            # prefer mrsa_label_y if present (from training file)
            if "mrsa_label_y" in src_cols:
                df["mrsa_label"] = df["mrsa_label_y"]
            else:
                df["mrsa_label"] = df[src_cols[0]]

            # drop all old mrsa_label_* columns
            df = df.drop(columns=src_cols)
            return df

        l1 = coalesce_label(l1)
        l4 = coalesce_label(l4)

    # finally, drop rows without label
    if "mrsa_label" in l1.columns:
        l1 = l1.dropna(subset=["mrsa_label"])
    if "mrsa_label" in l4.columns:
        l4 = l4.dropna(subset=["mrsa_label"])

    print("Merged Light-1 with labels:", l1.shape)
    print("Merged Light-4 with labels:", l4.shape)
    print(f"Columns after merge - L1: {l1.columns.tolist()}")
    print(f"Columns after merge - L4: {l4.columns.tolist()}")

    return l1, l4



def save_outputs(l1, l4, colmap):
    out1 = DATA_PROCESSED / "mrsa_light1_clean.parquet"
    out4 = DATA_PROCESSED / "mrsa_light4_clean.parquet"
    dictfile = DATA_PROCESSED / "mrsa_dictionary.json"

    l1.to_parquet(out1)
    l4.to_parquet(out4)

    with open(dictfile, "w", encoding="utf-8") as f:
        json.dump(colmap, f, indent=4)

    print("Saved:")
    print(" →", out1)
    print(" →", out4)
    print(" →", dictfile)


def main():
    print("=== MRSA PREPROCESSOR STARTED ===")

    # Load all datasets
    train_df = load_csv(FILE_TRAIN)
    l1_raw = load_csv(FILE_L1)
    l4_raw = load_csv(FILE_L4)

    # Clean column names + remove leakage
    l1_clean, l1_cols = clean_columns(l1_raw)
    l4_clean, l4_cols = clean_columns(l4_raw)
    train_clean, train_cols = clean_columns(train_df)

    # Merge MRSA labels
    l1_final, l4_final = merge_training(train_clean, l1_clean, l4_clean)

    # Save output + column dictionary
    colmap = {
        "training_columns_original": train_cols,
        "light1_columns_original": l1_cols,
        "light4_columns_original": l4_cols,
        "light1_clean_columns": l1_final.columns.tolist(),
        "light4_clean_columns": l4_final.columns.tolist()
    }

    save_outputs(l1_final, l4_final, colmap)

    print("\n=== MRSA PREPROCESSOR COMPLETED SUCCESSFULLY ===")


if __name__ == "__main__":
    main()
