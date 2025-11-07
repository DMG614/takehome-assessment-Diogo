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
is_electric = high_mpg['fuelType'].str.contains('Electric', case=False, na=False)

# Keep only NON-electric vehicles with high MPG (these are errors)
high_mpg_non_electric = high_mpg[is_electric == False]

print(f"Non-electric vehicles with MPG > 200: {len(high_mpg_non_electric)}")
print(f"PASS: No invalid high MPG values" if len(high_mpg_non_electric) == 0 else f"FAIL: Found {len(high_mpg_non_electric)} invalid high MPG values")

# Electric vehicles with high MPGe (should be allowed)
high_mpg_electric = high_mpg[high_mpg['fuelType'].str.contains('Electric', case=False, na=False)]
print(f"Electric vehicles with MPGe > 200: {len(high_mpg_electric)} (allowed)")

# Future years
current_year = datetime.now().year
future_years = len(epa_df[epa_df['year'] > current_year])
print(f"Records with future years (>{current_year}): {future_years}")
print(f"PASS: No future years" if future_years == 0 else f"FAIL: Found {future_years} future year records")

# Test 5: Duplicate Detection
print(f"\nTEST 5: Duplicate Detection")
key_fields = ['year', 'make', 'model', 'displ', 'cylinders', 'trany',
              'drive', 'fuelType', 'comb08', 'city08', 'highway08']

# Check if all key fields exist
existing_key_fields = [f for f in key_fields if f in epa_df.columns]
duplicates = epa_df.duplicated(subset=existing_key_fields, keep=False)
duplicate_count = duplicates.sum()
print(f"Exact duplicates found: {duplicate_count}")
print(f"PASS: No duplicates" if duplicate_count == 0 else f"FAIL: Found {duplicate_count} duplicate records")

if duplicate_count > 0:
    print("\nSample duplicates:")
    print(epa_df[duplicates][['year', 'make', 'model', 'comb08']].head(10))

# Test 6: Data Distribution Analysis
print(f"\nTEST 6: Data Distribution Analysis")
print(f"\nMPG Statistics:")
print(f"  Mean: {epa_df['comb08'].mean():.2f}")
print(f"  Median: {epa_df['comb08'].median():.2f}")
print(f"  Min: {epa_df['comb08'].min():.2f}")
print(f"  Max: {epa_df['comb08'].max():.2f}")
print(f"  Std Dev: {epa_df['comb08'].std():.2f}")

print(f"\nTop 5 Makes by Record Count:")
print(epa_df['make'].value_counts().head())

print(f"\nFuel Type Distribution:")
print(epa_df['fuelType'].value_counts())

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
print("EPA VALIDATION SUMMARY")
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
print("2. NHTSA Complaints - VALIDATION TESTS")
print("(Not yet implemented - waiting for process_nhtsa.py)")

# 3. DOE FUEL STATIONS - VALIDATION TESTS 
print("3. DOE Fuel Stations - VALIDATION TESTS")
print("(Not yet implemented - waiting for process_doe.py)")
