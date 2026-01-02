import pandas as pd

# Load dataset
df = pd.read_excel(r'd:\Yohan\Project\Raw\Version_1_9_Final_Clean_NoMissing.xlsx')

print("="*80)
print("CRITICAL DATA EXPLORATION")
print("="*80)

# Show sample records
print("\nFirst 10 records (selected columns):")
cols_to_show = ['Date', 'Organism', 'Sub Organism', 'Organism_Group', 'Ward / Ward No', 
                'Antibiotic [Meropenem  (MEM)]', 'Antibiotic [Piperacillin_Tazobactam  (TZP/PTZ)]']
print(df[cols_to_show].head(10).to_string())

print("\n" + "="*80)
print("ORGANISM ANALYSIS")
print("="*80)

# Check which organism column has data
print(f"\nOrganism column - Non-null count: {df['Organism'].notna().sum()}")
print(f"Sub Organism column - Non-null count: {df['Sub Organism'].notna().sum()}")
print(f"Organism_Group column - Non-null count: {df['Organism_Group'].notna().sum()}")

if df['Sub Organism'].notna().sum() > 0:
    print("\nSub Organism distribution:")
    print(df['Sub Organism'].value_counts())

if df['Organism_Group'].notna().sum() > 0:
    print("\nOrganism_Group distribution:")
    print(df['Organism_Group'].value_counts())

print("\n" + "="*80)
print("NON-FERMENTER DETECTION")
print("="*80)

# Check for non-fermenters in all organism columns
for col in ['Organism', 'Sub Organism', 'Organism_Group']:
    if df[col].notna().sum() > 0:
        df['temp_str'] = df[col].astype(str)
        nf_count = df['temp_str'].str.contains('Pseudomonas|Acinetobacter', case=False, na=False).sum()
        print(f"\n{col}: {nf_count} non-fermenter records")
        if nf_count > 0:
            nf_df = df[df['temp_str'].str.contains('Pseudomonas|Acinetobacter', case=False, na=False)]
            print(nf_df[col].value_counts())

print("\n" + "="*80)
print("ANTIBIOTIC DATA SAMPLE")
print("="*80)

# Show a few antibiotic results
ab_cols = [col for col in df.columns if 'Antibiotic [' in col][:5]
print(f"\nSample antibiotic columns ({len(ab_cols)} shown):")
for col in ab_cols:
    print(f"\n{col}:")
    print(df[col].value_counts())

print("\n" + "="*80)
print("WARD DISTRIBUTION")
print("="*80)
print(df['Ward / Ward No'].value_counts())

print("\nAnalysis complete!")
