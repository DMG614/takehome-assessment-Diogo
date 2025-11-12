import pandas as pd
import os
from datetime import datetime

os.makedirs('data/processed', exist_ok=True)

print("Initiate EPA data processing:")
# 1. Load raw data
df = pd.read_csv('data/raw/vehicles.csv', low_memory=False)
print(f"Initial records: {len(df):,}")

inital_df_len = len(df)

# 2. Filter to 2010+
print("\nFilter to 2010+:")
df = df[df['year'] >= 2010]
print(f"After filtering by from 2010 forward, the len is now: {len(df):,} and there were {len(df)/inital_df_len*100:.1f}% retained")

# 3. Drop rows with missing critical fields
print("\nRemove records with missing critical fields:")
before_missing_len = len(df)
# Must have: year, make, model, at least one MPG column
df = df.dropna(subset=['year', 'make', 'model'])
# Must have at least one MPG value (comb08, city08, or highway08)
# used notna() to check if values are not null/missing. Returns True if the value exists (not NaN, None nor missing) and false if the value is missing, nan or null
# After this line of code, I'll have the df with no missing values
df = df[(df['comb08'].notna()) | (df['city08'].notna()) | (df['highway08'].notna())]

print(f"Dropped {before_missing_len - len(df):,} records with missing critical fields")
print(f"Remaining: {len(df):,} records")

# 4. Remove obvious outliers
print("\nRemove obvious outliers")
before_outliers_len = len(df)

# Remove MPG = 0 (clearly invalid)
# MPG = Miles Per Gallon
df = df[df['comb08'] != 0]

# Remove MPG > 200 unless it's an electric vehicle (MPGe) - this is explained on the assumptions section in docs (processing_strategy.md)
# Check if fuelType contains "Electricity" or "Electric"
df = df[
    (df['comb08'] <= 200) |
    (df['fuelType'].str.contains('Electric', case=False, na=False))
]

# Remove future years (data quality issue)
current_year = datetime.now().year
df = df[df['year'] <= current_year]

print(f"Removed {before_outliers_len - len(df):,} outlier records")
print(f"Remaining: {len(df):,} records")

# 5. Remove exact duplicates
print("\nRemove exact duplicates")
before_dupes_len = len(df)
# Consider a duplicate if ALL these fields match
'''
Thought about usng Window Functions, but in this case we don't need it because, here, if these 11 fields match exactly, it's considered a system
duplicate. In this case, it should be removed. No need to rank it, just to remove it.
'''
key_fields = ['year', 'make', 'model', 'displ', 'cylinders', 'trany',
              'drive', 'fuelType', 'comb08', 'city08', 'highway08']
df = df.drop_duplicates(subset=key_fields, keep='first')
print(f"Removed {before_dupes_len - len(df):,} exact duplicates")
print(f"Remaining: {len(df):,} records")



# 6. Select relevant columns only (reduce from 84 to essentials)
print("\nSelect relevant columns")
columns_to_keep = [
    'year', 'make', 'model',
    'VClass',  # Vehicle class (sedan, SUV, etc.)
    'drive',  # Drive type (FWD, RWD, AWD)
    'trany',  # Transmission
    'cylinders',
    'displ',  # Engine specs
    'fuelType1',
    'fuelType2',  # Keep both fuel types for dual-fuel handling
    'city08',
    'highway08',
    'comb08',  # MPG ratings
    'co2TailpipeGpm',  # Emissions
    'id'  # Keep ID for reference
]

# Only keep columns that exist in the dataframe
columns_to_keep = [col for col in columns_to_keep if col in df.columns]
df = df[columns_to_keep]

# Rename fuel type columns to be more semantic
df = df.rename(columns={
    'fuelType1': 'primary_fuel',
    'fuelType2': 'secondary_fuel'
})

print(f"Reduced from 84 to {len(columns_to_keep)} columns")

# 7. Handle dual-fuel vehicles (explode into multiple rows)
print("\nHandle dual-fuel vehicles:")
before_explosion_len = len(df)

# Identify vehicles with secondary fuel type
dual_fuel_vehicles = df[df['secondary_fuel'].notna()].copy()
print(f"Found {len(dual_fuel_vehicles):,} dual-fuel vehicles")

# Create two separate dataframes:
# 1. All vehicles with their primary fuel
df_primary = df.copy()
df_primary['fuel_used'] = df_primary['primary_fuel']
df_primary['fuel_rank'] = 1

# 2. Dual-fuel vehicles with their secondary fuel
df_secondary = dual_fuel_vehicles.copy()
df_secondary['fuel_used'] = df_secondary['secondary_fuel']
df_secondary['fuel_rank'] = 2

# Combine both dataframes
df = pd.concat([df_primary, df_secondary], ignore_index=True)

print(f"Exploded {len(dual_fuel_vehicles):,} dual-fuel vehicles into {len(dual_fuel_vehicles) * 2:,} rows")
print(f"Total records after explosion: {len(df):,} (was {before_explosion_len:,})")
print(f"Added {len(df) - before_explosion_len:,} rows for secondary fuel types")

# 8. Save cleaned data
print("\nSave cleaned data")
output_path = 'data/processed/epa_vehicles_clean.csv'
df.to_csv(output_path, index=False)
print(f"Saved to: {output_path}")

# Summary
print("\nEnd of EPA processing")
print(f"Started with: {inital_df_len:,} raw records")
print(f"After cleaning: {before_explosion_len:,} unique vehicles")
print(f"After dual-fuel explosion: {len(df):,} vehicle-fuel combinations")
print(f"Note: Rows now represent vehicle-fuel combinations, not just vehicles")
print(f"Columns: 84 → {len(df.columns)}")
