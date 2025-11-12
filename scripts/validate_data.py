"""
Data validation checks for integrated datasets.

Runs basic sanity checks:
- Required columns exist
- Key fields aren't null
- Values are in reasonable ranges
- Minimum row counts met
"""

import pandas as pd
import sys


def check_file(path, required_cols, min_rows=100):
    """Check if a file exists and has expected structure."""
    try:
        df = pd.read_csv(path)
    except FileNotFoundError:
        print(f"Missing: {path}")
        return False

    # Check columns
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        print(f"{path}: missing columns {missing}")
        return False

    # Check row count
    if len(df) < min_rows:
        print(f"{path}: only {len(df)} rows (expected >{min_rows})")
        return False

    print(f"{path}: {len(df):,} rows")
    return True


def validate_vehicles(df):
    """
    Check vehicle data quality.

    Note: After dual-fuel vehicle explosion, rows represent vehicle-fuel
    combinations, not unique vehicles. Dual-fuel vehicles appear twice.
    """
    issues = []

    # Year range (EPA data filtered to 2010+)
    if df['year'].min() < 2010 or df['year'].max() > 2025:
        issues.append(f"year out of range: {df['year'].min()}-{df['year'].max()}")

    # MPG positive
    if (df['comb08'] <= 0).any():
        issues.append(f"{(df['comb08'] <= 0).sum()} vehicles with MPG ≤ 0")

    # Key fields not null
    for col in ['year', 'make', 'model']:
        nulls = df[col].isna().sum()
        if nulls > 0:
            issues.append(f"{nulls} null values in {col}")

    return issues


# Files to validate
# Note: Row count expectations updated for dual-fuel vehicle explosion
# (~1,547 dual-fuel vehicles × 2 = ~3,094 additional rows)
files = [
    ('data/integrated/vehicle_complaints_analysis.csv',
     ['year', 'make', 'model', 'comb08', 'total_complaints'],
     20000),  # Expect ~21,357 vehicle-fuel combinations

    ('data/integrated/fuel_infrastructure_analysis.csv',
     ['year', 'fuel_type_code', 'vehicle_count', 'total_stations'],
     30),  # Small dataset: fuel types by year (~43 rows)

    ('data/integrated/comprehensive_vehicle_analysis.csv',
     ['year', 'make', 'model', 'comb08', 'total_complaints', 'stations_nationwide'],
     20000)  # Expect ~21,357 vehicle-fuel combinations
]

check_problems = True

# Check each file
for path, cols, min_rows in files:
    if not check_file(path, cols, min_rows):
        check_problems = False

# Extra checks on main dataset
print("\nData quality checks:")
try:
    df = pd.read_csv('data/integrated/vehicle_complaints_analysis.csv')
    issues = validate_vehicles(df)

    if issues:
        for issue in issues:
            print(f"⚠ {issue}")
        check_problems = False
    else:
        print("All checks passed")

except Exception as e:
    print(f"Validation failed: {e}")
    check_problems = False

print()

if not check_problems:
    print("Validation failed\n")
    sys.exit(1)
else:
    print("Validation complete\n")
