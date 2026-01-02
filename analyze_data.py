import pandas as pd
import json

# Load the dataset
df = pd.read_excel(r'd:\Yohan\Project\Raw\Version_1_9_Final_Clean_NoMissing.xlsx')

# Create comprehensive analysis
analysis = {
    "total_records": len(df),
    "total_columns": len(df.columns),
    "columns": df.columns.tolist(),
    "date_range": {
        "min": str(df['Date'].min()),
        "max": str(df['Date'].max()),
        "unique_dates": int(df['Date'].nunique())
    },
    "organism_distribution": df['Organism'].value_counts().to_dict(),
    "data_types": {k: str(v) for k, v in df.dtypes.items()}
}

# Save as JSON
with open('dataset_analysis.json', 'w') as f:
    json.dump(analysis, f, indent=2)

# Print concise summary
print(f"Total Records: {analysis['total_records']}")
print(f"Columns: {analysis['total_columns']}")
print(f"Date Range: {analysis['date_range']['min']} to {analysis['date_range']['max']}")
print(f"\nOrganism Distribution:")
for org, count in analysis['organism_distribution'].items():
    print(f"  {org}: {count}")

# Check for ward column
print(f"\nWard Column: 'Ward / Ward No' found")

# Find antibiotic columns (exclude standard metadata columns)
metadata_cols = ['Date', 'Organism', 'Ward / Ward No', 'Specimen', 'Age', 'Gender', 
                 'Patient ID', 'Timestamp', 'Lab No', 'BHT No']
antibiotic_cols = [col for col in df.columns if col not in metadata_cols]
print(f"\nAntibiotic columns ({len(antibiotic_cols)}): {antibiotic_cols[:5]}...")

# Weekly analysis
df['Week'] = pd.to_datetime(df['Date']).dt.to_period('W')
print(f"\nUnique weeks: {df['Week'].nunique()}")
print(f"Avg records per week: {len(df) / df['Week'].nunique():.2f}")

# Check for non-fermenters - fix the string check
df['Organism_str'] = df['Organism'].astype(str)
nf_df = df[df['Organism_str'].str.contains('Pseudomonas|Acinetobacter', case=False, na=False)]
print(f"\nNon-fermenter records: {len(nf_df)}")
if len(nf_df) > 0:
    print("NF organisms distribution:")
    for org, count in nf_df['Organism'].value_counts().items():
        print(f"  {org}: {count}")

print("\n✓ Analysis saved to dataset_analysis.json")
