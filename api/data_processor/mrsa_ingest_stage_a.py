import pandas as pd
from sqlalchemy import create_engine, text
import os

# ── DATABASE CONNECTION ────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ast_user:ast_password_2024@db:5432/ast_db")
engine = create_engine(DATABASE_URL)


def map_cell_count(raw_value) -> str:
    """
    Convert raw microscopy cell count text → LOW / MEDIUM / HIGH.
    Handles both new dataset format (<10, 10-25, >25) and old free-text lab variants.
    """
    val = str(raw_value).strip().lower()

    # New dataset exact values
    if val in ['<10', '< 10', '10']:
        return 'LOW'
    if val in ['10-25', '10 - 25', '10–25']:
        return 'MEDIUM'
    if val in ['>25', '> 25', '25']:
        return 'HIGH'

    # Legacy free-text fallback
    if any(x in val for x in ['none', '0', 'no wc', 'not seen', 'rare', 'scanty',
                                '-', 'negative', 'nil', '+', '<10', '< 10']):
        return 'LOW'
    elif any(x in val for x in ['few', '++', 'moderate', 'medium', 'occasional']):
        return 'MEDIUM'
    elif any(x in val for x in ['many', '+++', 'plenty', '>25', '> 25',
                                  'numerous', 'heavy', 'packed', '++++', 'abundant']):
        return 'HIGH'

    return 'LOW'  # safe default


def run_mrsa_stage_a():
    print("🧪 Starting MRSA Stage A: Ingestion & Scope Control — Schema v2...")

    # 1. READ RAW FILE — updated to realistic overlap dataset
    file_path = "/app/data/raw/MRSA_NEW02.xlsx"
    fallback_v1 = "/app/data/raw/MRSA_NEW.xlsx"
    fallback_v0 = "/app/data/raw/MRSA_Synthetic_PreAST_Training_12000.xlsx"

    if os.path.exists(file_path):
        print(f"   - Using realistic dataset: {file_path}")
    elif os.path.exists(fallback_v1):
        file_path = fallback_v1
        print(f"   - MRSA_NEW02 not found. Falling back to: {fallback_v1}")
    elif os.path.exists(fallback_v0):
        file_path = fallback_v0
        print(f"   - Falling back to original synthetic dataset: {fallback_v0}")
    else:
        print(f"❌ Error: No dataset found.")
        return

    df = pd.read_excel(file_path)
    initial_count = len(df)
    print(f"   - Loaded {initial_count} rows.")

    # 2. NORMALIZE COLUMN NAMES
    df.columns = [c.strip().replace(" ", "_") for c in df.columns]
    print(f"   - Columns: {list(df.columns)}")

    # 3. FILTER SCOPE — Staphylococci only
    # New dataset uses 'Organism' column; all rows are Staphylococcus aureus
    if 'Organism_Group' in df.columns:
        mask_staph = (
            df['Organism_Group'].astype(str).str.contains('Staphy', case=False, na=False) |
            df['Organism'].astype(str).str.contains('Staphy', case=False, na=False)
        )
    elif 'Organism' in df.columns:
        mask_staph = df['Organism'].astype(str).str.contains('Staphy', case=False, na=False)
    else:
        # No organism filter possible — use all rows
        mask_staph = pd.Series([True] * len(df))
        print("   ⚠️  No Organism column found — using all rows.")

    df_scope = df[mask_staph].copy()
    print(f"   - Filtered Staphylococci Scope: {len(df_scope)} rows "
          f"(Rejected {initial_count - len(df_scope)})")

    # 4. GROUND TRUTH LABEL
    # Support both column names: 'Sub_Organism' and 'mrsa_label'
    if 'mrsa_label' in df_scope.columns:
        df_scope['mrsa_label'] = df_scope['mrsa_label'].astype(int)
    elif 'Sub_Organism' in df_scope.columns:
        df_scope['mrsa_label'] = df_scope['Sub_Organism'].apply(
            lambda x: 1 if str(x).strip().upper() == 'MRSA' else 0
        )
    else:
        print("❌ Error: Cannot find 'Sub_Organism' or 'mrsa_label' column.")
        return

    label_counts = df_scope['mrsa_label'].value_counts()
    print(f"   - Ground Truth: MRSA={label_counts.get(1, 0)}, non-MRSA={label_counts.get(0, 0)}")

    # 5. BUILD CLEAN DATASET — Schema v2 columns only
    # Supports both old column names and new dataset column names
    clean_df = pd.DataFrame()
    clean_df['mrsa_label'] = df_scope['mrsa_label'].values

    clean_df['ward'] = (
        df_scope.get('Ward', df_scope.get('Ward_No', pd.Series(['Unknown'] * len(df_scope))))
        .fillna('Unknown').astype(str)
    )

    clean_df['sample_type'] = (
        df_scope.get('Sample_Type', pd.Series(['Unknown'] * len(df_scope)))
        .fillna('Unknown').astype(str)
    )

    # Gram stain — new dataset uses 'Gram_Stain', old used 'Gram_Positivity'
    gram_col = (
        df_scope.get('Gram_Stain')
        if 'Gram_Stain' in df_scope.columns
        else df_scope.get('Gram_Positivity')
    )
    clean_df['gram_stain'] = (gram_col if gram_col is not None
                               else pd.Series(['Unknown'] * len(df_scope))).fillna('Unknown').astype(str)

    # Cell count → category (new dataset already has text format, old had numeric/mixed)
    raw_cell = df_scope.get('Cell_Count', pd.Series(['unknown'] * len(df_scope)))
    clean_df['cell_count_category'] = raw_cell.apply(map_cell_count)

    # Growth time — numeric hours, NULL for non-blood
    growth_col = df_scope.get('Growth_Time', df_scope.get('Growth_Time_After'))
    clean_df['growth_time'] = (
        pd.to_numeric(growth_col, errors='coerce') if growth_col is not None else None
    )

    # Recent antibiotic use
    ab_col = df_scope.get('Recent_Antibiotic_Use')
    if ab_col is None:
        print("   ⚠️  Recent_Antibiotic_Use not found — defaulting to 'Unknown'")
        clean_df['recent_antibiotic_use'] = 'Unknown'
    else:
        clean_df['recent_antibiotic_use'] = ab_col.fillna('Unknown').astype(str)

    # Length of stay
    los_col = df_scope.get('Length_Of_Stay')
    if los_col is None:
        print("   ⚠️  Length_Of_Stay not found — defaulting to 0")
        clean_df['length_of_stay'] = 0
    else:
        clean_df['length_of_stay'] = pd.to_numeric(los_col, errors='coerce').fillna(0).astype(int)

    # BHT / Lab number for tracing — kept out of model
    bht_col = df_scope.get('Lab_No', df_scope.get('BHT', df_scope.get('BHT_No')))
    clean_df['bht'] = bht_col if bht_col is not None else None

    print(f"   - Cleaned DataFrame shape: {clean_df.shape}")
    print(f"   - Columns: {list(clean_df.columns)}")
    print(f"   - recent_antibiotic_use values: {clean_df['recent_antibiotic_use'].value_counts().to_dict()}")
    print(f"   - cell_count_category values: {clean_df['cell_count_category'].value_counts().to_dict()}")

    # 6. LOAD INTO DATABASE
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE mrsa_raw_clean RESTART IDENTITY;"))
        conn.commit()
        print("   - Table truncated.")

    clean_df.to_sql('mrsa_raw_clean', engine, if_exists='append', index=False)
    print(f"✅ Stage A Complete: {len(clean_df)} rows ingested (Schema v2, new dataset).")


if __name__ == "__main__":
    run_mrsa_stage_a()
