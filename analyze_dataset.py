import pandas as pd
import numpy as np

# Load the dataset
df = pd.read_excel(r'd:\Yohan\Project\Raw\Version_1_9_Final_Clean_NoMissing.xlsx')

print('=' * 80)
print('DATASET OVERVIEW')
print('=' * 80)
print(f'Total Records: {len(df)}')
print(f'Total Columns: {len(df.columns)}')
print(f'\nColumn Names:')
for i, col in enumerate(df.columns, 1):
    print(f'  {i}. {col}')

print('\n' + '=' * 80)
print('SAMPLE DATA (First 5 rows)')
print('=' * 80)
print(df.head().to_string())

print('\n' + '=' * 80)
print('DATA TYPES')
print('=' * 80)
print(df.dtypes)

print('\n' + '=' * 80)
print('ORGANISM DISTRIBUTION')
print('=' * 80)
print(df['Organism'].value_counts())

print('\n' + '=' * 80)
print('DATE ANALYSIS')
print('=' * 80)
print(f'Date Range: {df["Date"].min()} to {df["Date"].max()}')
print(f'Unique Dates: {df["Date"].nunique()}')
print(f'\nAll unique dates:')
print(sorted(df['Date'].unique()))

print('\n' + '=' * 80)
print('WARD ANALYSIS')
print('=' * 80)
ward_col = 'Ward' if 'Ward' in df.columns else 'Ward No'
if ward_col in df.columns:
    print(f'{ward_col} distribution:')
    print(df[ward_col].value_counts())

print('\n' + '=' * 80)
print('ANTIBIOTIC COLUMNS ANALYSIS')
print('=' * 80)
# Find antibiotic columns (typically those with S/I/R values)
antibiotic_cols = [col for col in df.columns if col not in ['Date', 'Organism', 'Ward', 'Ward No', 'Specimen']]
print(f'Antibiotic columns found: {len(antibiotic_cols)}')
print(f'\nAntibiotic columns:')
for col in antibiotic_cols[:10]:  # Show first 10
    print(f'  - {col}')
if len(antibiotic_cols) > 10:
    print(f'  ... and {len(antibiotic_cols) - 10} more')

print('\n' + '=' * 80)
print('DATA SPARSITY ANALYSIS')
print('=' * 80)
# Weekly grouping analysis
df['Week'] = pd.to_datetime(df['Date']).dt.to_period('W')
weeks_with_data = df['Week'].nunique()
print(f'Unique weeks with data: {weeks_with_data}')
print(f'Records per week (average): {len(df) / weeks_with_data:.2f}')

# Non-fermenter specific
non_fermenters = df[df['Organism'].isin(['Pseudomonas aeruginosa', 'Acinetobacter spp.', 'Acinetobacter baumannii'])]
print(f'\nNon-fermenter records: {len(non_fermenters)}')
print(f'Non-fermenter organisms:')
print(non_fermenters['Organism'].value_counts())
