import pandas as pd
import numpy as np
from datetime import datetime

# 1. EPA VEHICLE DATA VALIDATION

print("1. Epa Vehicle Data - validation tests")

epa_df = pd.read_csv('data/processed/epa_vehicles_clean.csv')

print(f"\nTEST 1: Basic Statistics")
print(f"Count of Records: {len(epa_df):,}")
print(f"Total columns: {len(epa_df.columns)}")
print(f"Columns: {list(epa_df.columns)}")

# Test 2: Temporal Filter (should only have 2010+)
print(f"\nTEST 2: Temporal Filter Validation")
min_year = epa_df['year'].min()
max_year = epa_df['year'].max()
pre_2010 = len(epa_df[epa_df['year'] < 2010])
print(f"Year range: {min_year} - {max_year}")
print(f"Records before 2010: {pre_2010}")
print(f"PASS: All records from 2010+" if pre_2010 == 0 else f"FAIL: Found {pre_2010} records before 2010")

# Test 3: Missing Critical Fields
print(f"\nTEST 3: Missing Critical Fields")
critical_fields = ['year', 'make', 'model', 'comb08']
missing_counts = {}
for field in critical_fields:
    missing = epa_df[field].isna().sum()
    missing_counts[field] = missing
    print(f"{field}: {missing} missing values")

all_critical_complete = all(count == 0 for count in missing_counts.values())
print(f"PASS: No missing critical fields" if all_critical_complete else f"FAIL: Found missing critical fields")

# Test 4: Outlier Detection - MPG Values
print(f"\nTEST 4: Outlier Detection - MPG Values")
mpg_zero = len(epa_df[epa_df['comb08'] == 0])
print(f"Records with MPG = 0: {mpg_zero}")
print(f"PASS: No zero MPG values" if mpg_zero == 0 else f"FAIL: Found {mpg_zero} zero MPG values")

# Check for MPG > 200 in non-electric vehicles
high_mpg = epa_df[epa_df['comb08'] > 200]

# Identify which vehicles are electric (high MPGe is normal for EVs)
is_electric = high_mpg['fuel_used'].str.contains('Electric', case=False, na=False)

# Keep only NON-electric vehicles with high MPG (these are errors)
high_mpg_non_electric = high_mpg[is_electric == False]

print(f"Non-electric vehicles with MPG > 200: {len(high_mpg_non_electric)}")
print(f"PASS: No invalid high MPG values" if len(high_mpg_non_electric) == 0 else f"FAIL: Found {len(high_mpg_non_electric)} invalid high MPG values")

# Electric vehicles with high MPGe (should be allowed)
high_mpg_electric = high_mpg[high_mpg['fuel_used'].str.contains('Electric', case=False, na=False)]
print(f"Electric vehicles with MPGe > 200: {len(high_mpg_electric)} (allowed)")

# Future years
current_year = datetime.now().year
future_years = len(epa_df[epa_df['year'] > current_year])
print(f"Records with future years (>{current_year}): {future_years}")
print(f"PASS: No future years" if future_years == 0 else f"FAIL: Found {future_years} future year records")

# Test 5: Duplicate Detection
print(f"\nTEST 5: Duplicate Detection")
# After dual-fuel explosion, check for true duplicates by ID
# The same vehicle ID should appear at most twice (once for each fuel_rank if dual-fuel)
print(f"Note: After dual-fuel explosion, each vehicle can appear 1-2 times")

# Check for duplicate IDs with same fuel_rank (these would be true duplicates)
id_rank_duplicates = epa_df.duplicated(subset=['id', 'fuel_rank'], keep=False)
duplicate_count = id_rank_duplicates.sum()
print(f"True duplicates found (same ID + fuel_rank): {duplicate_count}")

# Check dual-fuel vehicle distribution
fuel_rank_dist = epa_df.groupby('id')['fuel_rank'].nunique()
dual_fuel_vehicles = (fuel_rank_dist == 2).sum()
single_fuel_vehicles = (fuel_rank_dist == 1).sum()
print(f"Single-fuel vehicles: {single_fuel_vehicles:,}")
print(f"Dual-fuel vehicles: {dual_fuel_vehicles:,}")

# Verify vehicle-fuel combination uniqueness
# Note: Different vehicles can have identical specs (year/make/model/MPG)
# This is expected - e.g., 2010 Malibu has multiple trim levels with same MPG
unique_combinations = len(epa_df)
unique_ids = epa_df['id'].nunique()
print(f"Total vehicle-fuel combinations: {unique_combinations:,}")
print(f"Unique vehicle IDs: {unique_ids:,}")

print(f"PASS: No duplicate ID+fuel_rank combinations" if duplicate_count == 0 else f"FAIL: Found {duplicate_count} true duplicate records")

if duplicate_count > 0:
    print("\nSample true duplicates (same ID + fuel_rank):")
    print(epa_df[id_rank_duplicates][['year', 'make', 'model', 'fuel_used', 'fuel_rank', 'id']].head(10))

# Test 6: Data Distribution Analysis
print(f"\nTEST 6: Data Distribution Analysis")
print(f"\nMPG Statistics:")
print(f" - Mean: {epa_df['comb08'].mean():.2f}")
print(f" - Median: {epa_df['comb08'].median():.2f}")
print(f" - Min: {epa_df['comb08'].min():.2f}")
print(f" - Max: {epa_df['comb08'].max():.2f}")
print(f" - Std Dev: {epa_df['comb08'].std():.2f}")

print(f"\nTop 5 Makes by Record Count:")
print(epa_df['make'].value_counts().head())

print(f"\nFuel Type Distribution:")
print(epa_df['fuel_used'].value_counts())

print(f"\nYear Distribution:")
print(epa_df['year'].value_counts().sort_index())

# Test 7: Data Type Validation
print(f"\nTEST 7: Data Type Validation")
print(f"\nColumn Data Types:")
print(epa_df.dtypes)

# Check if numeric columns are actually numeric
numeric_columns = ['year', 'cylinders', 'displ', 'city08', 'highway08', 'comb08', 'co2TailpipeGpm']
for col in numeric_columns:
    if col in epa_df.columns:
        is_numeric = pd.api.types.is_numeric_dtype(epa_df[col])
        print(f"{col}: {'✓' if is_numeric else '✗'} {epa_df[col].dtype}")

# Test 8: Consistency Checks
print(f"\nTEST 8: Consistency Checks")

# Combined MPG should be between min and max of city and highway
# Note: Hybrids can have city > highway due to regenerative braking
if all(col in epa_df.columns for col in ['city08', 'highway08', 'comb08']):
    min_mpg = epa_df[['city08', 'highway08']].min(axis=1)
    max_mpg = epa_df[['city08', 'highway08']].max(axis=1)

    inconsistent = epa_df[
        (epa_df['comb08'] < min_mpg) |
        (epa_df['comb08'] > max_mpg)
    ]
    print(f"Records where combined MPG is outside min/max range: {len(inconsistent)}")
    if len(inconsistent) > 0:
        print("Sample inconsistent records:")
        print(inconsistent[['year', 'make', 'model', 'city08', 'highway08', 'comb08']].head())

# Summary
print("EPA Validation Summary")
tests_passed = 0
tests_total = 6

if pre_2010 == 0:
    print("PASS: All records from 2010+")
    tests_passed += 1
else:
    print(f"FAIL: Found {pre_2010} records before 2010")

if all_critical_complete:
    print("PASS: No missing critical fields")
    tests_passed += 1
else:
    print("FAIL: Missing critical fields found")

if mpg_zero == 0:
    print("PASS: No zero MPG values")
    tests_passed += 1
else:
    print(f"FAIL: Found {mpg_zero} zero MPG values")

if len(high_mpg_non_electric) == 0:
    print("PASS: No invalid high MPG values")
    tests_passed += 1
else:
    print(f"FAIL: Found {len(high_mpg_non_electric)} invalid high MPG values")

if future_years == 0:
    print("PASS: No future years")
    tests_passed += 1
else:
    print(f"FAIL: Found {future_years} future year records")

if duplicate_count == 0:
    print("PASS: No duplicates")
    tests_passed += 1
else:
    print(f"FAIL: Found {duplicate_count} duplicate records")

print(f"\nTests passed: {tests_passed}/{tests_total}")

# 2. NHTSA COMPLAINTS - VALIDATION TESTS
print("2. NHTSA Complaints - validation tests")

nhtsa_df = pd.read_csv('data/processed/nhtsa_complaints_clean.csv')

print(f"\nTEST 1: Basic Statistics")
print(f"Count of Records: {len(nhtsa_df):,}")
print(f"Total columns: {len(nhtsa_df.columns)}")
print(f"Columns: {list(nhtsa_df.columns)}")

# Test 2: Missing Critical Fields
print(f"\nTEST 2: Missing Critical Fields")
critical_fields = ['ODINO', 'DATEA', 'YEARTXT', 'MAKETXT', 'MODELTXT']
missing_counts = {}
for field in critical_fields:
    missing = nhtsa_df[field].isna().sum()
    missing_counts[field] = missing
    print(f"{field}: {missing} missing values")

all_critical_complete = all(count == 0 for count in missing_counts.values())
print(f"PASS: No missing critical fields" if all_critical_complete else f"FAIL: Found missing critical fields")

# Test 3: Duplicate Detection
print(f"\nTEST 3: Duplicate Detection")
duplicates = nhtsa_df.duplicated(subset=['ODINO'], keep=False)
duplicate_count = duplicates.sum()
print(f"Exact duplicates found: {duplicate_count}")
print(f"PASS: No duplicates" if duplicate_count == 0 else f"FAIL: Found {duplicate_count} duplicate records")

# Test 4: Date Validation
print(f"\nTEST 4: Date Validation")
nhtsa_df['DATEA_parsed'] = pd.to_datetime(nhtsa_df['DATEA'], errors='coerce')
current_date = datetime.now()
future_dates = len(nhtsa_df[nhtsa_df['DATEA_parsed'] > current_date])
print(f"Records with future dates: {future_dates}")
print(f"PASS: No future dates" if future_dates == 0 else f"FAIL: Found {future_dates} future date records")

# Test 5: Year Range Validation
print(f"\nTEST 5: Year Range Validation")
min_year = nhtsa_df['YEARTXT'].min()
max_year = nhtsa_df['YEARTXT'].max()
current_year = datetime.now().year
future_years = len(nhtsa_df[nhtsa_df['YEARTXT'] > current_year])
print(f"Year range: {int(min_year)} - {int(max_year)}")
print(f"Records with future years (>{current_year}): {future_years}")
print(f"PASS: No future years" if future_years == 0 else f"FAIL: Found {future_years} future year records")

# Test 6: Data Distribution
print(f"\nTEST 6: Data Distribution Analysis")
print(f"\nTop 5 Makes by Complaint Count:")
print(nhtsa_df['MAKETXT'].value_counts().head())

print(f"\nYear Distribution:")
print(nhtsa_df['YEARTXT'].value_counts().sort_index())

print(f"\nCrash/Fire/Injury Statistics:")
if 'CRASH' in nhtsa_df.columns:
    print(f" - Complaints with crashes: {(nhtsa_df['CRASH'] == 'Y').sum():,}")
if 'FIRE' in nhtsa_df.columns:
    print(f" - Complaints with fires: {(nhtsa_df['FIRE'] == 'Y').sum():,}")
if 'INJURED' in nhtsa_df.columns:
    injured_count = nhtsa_df['INJURED'].sum()
    if pd.notna(injured_count):
        print(f" - Total injuries: {int(injured_count):,}")
if 'DEATHS' in nhtsa_df.columns:
    deaths_count = nhtsa_df['DEATHS'].sum()
    if pd.notna(deaths_count):
        print(f" - Total deaths: {int(deaths_count):,}")

# Summary
print("\nNHTSA Validation Summary:")
tests_passed = 0
tests_total = 4

if all_critical_complete:
    print("PASS: No missing critical fields")
    tests_passed += 1
else:
    print("FAIL: Missing critical fields found")

if duplicate_count == 0:
    print("PASS: No duplicates")
    tests_passed += 1
else:
    print(f"FAIL: Found {duplicate_count} duplicate records")

if future_dates == 0:
    print("PASS: No future dates")
    tests_passed += 1
else:
    print(f"FAIL: Found {future_dates} future date records")

if future_years == 0:
    print("PASS: No future years")
    tests_passed += 1
else:
    print(f"FAIL: Found {future_years} future year records")

print(f"\nTests passed: {tests_passed}/{tests_total}")

# 3. DOE FUEL STATIONS - VALIDATION TESTS
print("3. DOE Fuel Stations - validation tests")

doe_df = pd.read_csv('data/processed/doe_fuel_stations_clean.csv')

print(f"\nTEST 1: Basic Statistics")
print(f"Count of Records: {len(doe_df):,}")
print(f"Total columns: {len(doe_df.columns)}")
print(f"Columns: {list(doe_df.columns)}")

# Test 2: Missing Critical Fields
print(f"\nTEST 2: Missing Critical Fields")
critical_fields = ['latitude', 'longitude', 'fuel_type_code', 'status_code']
missing_counts = {}
for field in critical_fields:
    missing = doe_df[field].isna().sum()
    missing_counts[field] = missing
    print(f"{field}: {missing} missing values")

all_critical_complete = all(count == 0 for count in missing_counts.values())
print(f"PASS: No missing critical fields" if all_critical_complete else f"FAIL: Found missing critical fields")

# Test 3: Geographic Bounds Validation
print(f"\nTEST 3: Geographic Bounds Validation")
# Check for coordinates within U.S. bounds (including Alaska and Hawaii)
# Latitude: 18 (Hawaii) to 72 (Alaska)
# Longitude: -180 (Alaska) to -65 (East Coast)
out_of_bounds_lat = len(doe_df[(doe_df['latitude'] < 18) | (doe_df['latitude'] > 72)])
out_of_bounds_lon = len(doe_df[(doe_df['longitude'] < -180) | (doe_df['longitude'] > -65)])
zero_coords = len(doe_df[(doe_df['latitude'] == 0) & (doe_df['longitude'] == 0)])

print(f"Records with latitude out of bounds (18-72): {out_of_bounds_lat}")
print(f"Records with longitude out of bounds (-180 to -65): {out_of_bounds_lon}")
print(f"Records with coordinates at (0,0): {zero_coords}")

geographic_valid = (out_of_bounds_lat == 0 and out_of_bounds_lon == 0 and zero_coords == 0)
print(f"PASS: All coordinates within valid bounds" if geographic_valid else f"FAIL: Found invalid coordinates")

# Test 4: Fuel Type Validation
print(f"\nTEST 4: Fuel Type Validation")
valid_fuel_types = ['ELEC', 'LNG', 'CNG', 'BD', 'E85', 'HY']
invalid_fuel_types = doe_df[doe_df['fuel_type_code'].isin(valid_fuel_types) == False]
print(f"Records with invalid fuel types: {len(invalid_fuel_types)}")
print(f"PASS: All fuel types are alternative fuels" if len(invalid_fuel_types) == 0 else f"FAIL: Found {len(invalid_fuel_types)} invalid fuel types")

# Test 5: Duplicate Detection
print(f"\nTEST 5: Duplicate Detection")

duplicates = doe_df.duplicated(subset=['id'], keep=False)
duplicate_count = duplicates.sum()
print(f"Exact duplicates found (by ID): {duplicate_count}")

print(f"PASS: No duplicates" if duplicate_count == 0 else f"FAIL: Found {duplicate_count} duplicate records")

# Test 6: Data Distribution Analysis
print(f"\nTEST 6: Data Distribution Analysis")
print(f"\nFuel Type Distribution:")
print(doe_df['fuel_type_code'].value_counts())

print(f"\nTop 10 States by Station Count:")
if 'state' in doe_df.columns:
    print(doe_df['state'].value_counts().head(10))

print(f"\nStatus Distribution:")
if 'status_code' in doe_df.columns:
    print(doe_df['status_code'].value_counts())

print(f"\nAccess Type Distribution:")
if 'access_code' in doe_df.columns:
    print(doe_df['access_code'].value_counts())

# Summary
print("\nDOE Validation Summary:")
tests_passed = 0
tests_total = 4

if all_critical_complete:
    print("PASS: No missing critical fields")
    tests_passed += 1
else:
    print("FAIL: Missing critical fields found")

if geographic_valid:
    print("PASS: All coordinates within valid bounds")
    tests_passed += 1
else:
    print("FAIL: Found invalid coordinates")

if len(invalid_fuel_types) == 0:
    print("PASS: All fuel types are alternative fuels")
    tests_passed += 1
else:
    print(f"FAIL: Found {len(invalid_fuel_types)} invalid fuel types")

if duplicate_count == 0:
    print("PASS: No duplicates")
    tests_passed += 1
else:
    print(f"FAIL: Found {duplicate_count} duplicate records")

print(f"\nTests passed: {tests_passed}/{tests_total}")
