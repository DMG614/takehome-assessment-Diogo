import pandas as pd
import os
from datetime import datetime

os.makedirs('data/processed', exist_ok=True)

print("Initiate DOE fuel stations data processing:")

# 1. Load raw data
df = pd.read_csv('data/raw/alt_fuel_stations.csv', low_memory=False)
print(f"Initial records: {len(df):,}")

initial_df_len = len(df)

# 2. Drop rows with missing critical fields
print("\nRemove records with missing critical fields:")
before_missing_len = len(df)
# Must have: latitude, longitude, fuel_type_code, status_code
df = df.dropna(subset=['latitude', 'longitude', 'fuel_type_code', 'status_code'])

print(f"Dropped {before_missing_len - len(df):,} records with missing critical fields")
print(f"Remaining: {len(df):,} records")

# 3. Remove obvious outliers
print("\nRemove obvious outliers:")
before_outliers_len = len(df)

# Remove coordinates outside U.S. bounds
# Latitude 18-72: covers Hawaii to Alaska
# Longitude -180 to -65: covers West to East Coast (including Alaska and Hawaii)
# These ranges were assumed for this project to catch data entry errors
df = df[
    (df['latitude'] >= 18) & (df['latitude'] <= 72) &
    (df['longitude'] >= -180) & (df['longitude'] <= -65)
]

# Remove coordinates that are exactly 0,0 (data entry errors)
df = df[(df['latitude'] != 0) | (df['longitude'] != 0)]

print(f"Removed {before_outliers_len - len(df):,} outlier records")
print(f"Remaining: {len(df):,} records")

# 4. Remove exact duplicates
print("\nRemove exact duplicates:")
before_dupes_len = len(df)
# Each station has a unique ID from the NREL API
df = df.drop_duplicates(subset=['id'], keep='first')

print(f"Removed {before_dupes_len - len(df):,} exact duplicates")
print(f"Remaining: {len(df):,} records")

# 5. Filter to relevant fuel types
print("\nFilter to relevant alternative fuel types:")
before_fuel_filter_len = len(df)
# Keep only alternative fuels: ELEC, LNG, CNG, BD, E85, HY
# Remove gasoline/diesel stations if present
relevant_fuel_types = ['ELEC', 'LNG', 'CNG', 'BD', 'E85', 'HY']
df = df[df['fuel_type_code'].isin(relevant_fuel_types)]

print(f"Removed {before_fuel_filter_len - len(df):,} non-alternative fuel stations")
print(f"Remaining: {len(df):,} records")

# 6. Select relevant columns only
print("\nSelect relevant columns:")
columns_to_keep = [
    'fuel_type_code',  # Type of fuel
    'station_name',  # Station identifier
    'street_address',  # Location details
    'city',
    'state',
    'zip',
    'latitude',  # Coordinates
    'longitude',
    'status_code',  # Operational status
    'access_code',  # Public/private
    'open_date',  # When opened
    'ev_network',  # EV charging network (if applicable)
    'ev_connector_types',  # Connector types (if applicable)
    'ev_pricing',  # Pricing info (if applicable)
    'id'  # Keep ID for reference
]

# Only keep columns that exist in the dataframe
columns_to_keep = [col for col in columns_to_keep if col in df.columns]
df = df[columns_to_keep]
print(f"Reduced from 76 to {len(columns_to_keep)} columns")

# 7. Save cleaned data
print("\nSave cleaned data:")
output_path = 'data/processed/doe_fuel_stations_clean.csv'
df.to_csv(output_path, index=False)
print(f"Saved to: {output_path}")

# Summary
print("\nEnd of DOE processing:")
print(f"Started with: {initial_df_len:,} records")
print(f"Ended with:   {len(df):,} records")
print(f"Kept {len(df)/initial_df_len*100:.1f}% of original data")
print(f"Removed {initial_df_len - len(df):,} rows total")
print(f"Columns: 76 → {len(df.columns)}")
