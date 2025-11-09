import pandas as pd
import os
from datetime import datetime

os.makedirs('data/processed', exist_ok=True)

print("Initiate NHTSA complaints data processing:")

# 1. Load raw data
# File has no header row - column positions verified by manual inspection
# Read only the columns we need by index
df = pd.read_csv('data/raw/COMPLAINTS_RECEIVED_2020-2024.txt',
                 sep='\t',
                 header=None,
                 usecols=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 14, 17],
                 names=['ODINO', 'CMPLID', 'MFGTXT', 'MAKETXT', 'MODELTXT', 'YEARTXT',
                        'CRASH', 'DATEA', 'FIRE', 'INJURED', 'DEATHS', 'COMPDESC',
                        'VIN', 'MILEAGE'],
                 low_memory=False)
print(f"Initial records: {len(df):,}")

initial_df_len = len(df)

# 2. Drop rows with missing critical fields
print("\nRemove records with missing critical fields:")
before_missing_len = len(df)
df = df.dropna(subset=['ODINO', 'DATEA', 'YEARTXT', 'MAKETXT', 'MODELTXT'])

print(f"Dropped {before_missing_len - len(df):,} records with missing critical fields")
print(f"Remaining: {len(df):,} records")

# 3. Data type conversions and outlier removal
print("\nData type conversions and outlier removal:")
before_outliers_len = len(df)

# Convert DATEA from YYYYMMDD format to datetime
df['DATEA'] = pd.to_datetime(df['DATEA'].astype(str), format='%Y%m%d', errors='coerce')

# Convert YEARTXT to numeric
df['YEARTXT'] = pd.to_numeric(df['YEARTXT'], errors='coerce')

# Remove future dates
current_date = datetime.now()
df = df[(df['DATEA'].isna()) | (df['DATEA'] <= current_date)]

# Remove mileage > 1,000,000 miles (data entry errors)
df = df[(df['MILEAGE'].isna()) | (df['MILEAGE'] <= 1000000)]

# Remove future years
current_year = datetime.now().year
df = df[(df['YEARTXT'].isna()) | (df['YEARTXT'] <= current_year)]

print(f"Removed {before_outliers_len - len(df):,} outlier records")
print(f"Remaining: {len(df):,} records")

# 4. Remove exact duplicates
print("\nRemove exact duplicates:")
before_dupes_len = len(df)
df = df.drop_duplicates(subset=['ODINO'], keep='first')

print(f"Removed {before_dupes_len - len(df):,} exact duplicates")
print(f"Remaining: {len(df):,} records")

# 5. Convert DATEA to string format for CSV storage
df['DATEA'] = df['DATEA'].dt.strftime('%Y-%m-%d')

# 6. Convert numeric fields to integers (remove .0 formatting)
print("\nConvert numeric fields to proper integer types:")
# YEARTXT: convert to int (no nulls after filtering)
df['YEARTXT'] = df['YEARTXT'].astype(int)
# MILEAGE: convert to Int64 (nullable integer) to handle any potential nulls
df['MILEAGE'] = df['MILEAGE'].astype('Int64')

# 7. Save cleaned data
print("\nSave cleaned data:")
output_path = 'data/processed/nhtsa_complaints_clean.csv'
df.to_csv(output_path, index=False)
print(f"Saved to: {output_path}")

# Summary
print("\nEnd of NHTSA processing:")
print(f"Started with: {initial_df_len:,} records")
print(f"Ended with:   {len(df):,} records")
print(f"Kept {len(df)/initial_df_len*100:.1f}% of original data")
print(f"Removed {initial_df_len - len(df):,} rows total")
print(f"Columns: 49 → {len(df.columns)}")
