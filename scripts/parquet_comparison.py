"""
Parquet vs CSV comparison

Shows file size difference between CSV and Parquet formats.
Parquet is a columnar storage format that's more efficient for big data.
"""

import pandas as pd
import os


def format_size(bytes):
    """Convert bytes to human-readable format."""
    mb = bytes / (1024 * 1024)
    return f"{mb:.2f} MB"


# Load one of the integrated datasets
csv_path = 'data/integrated/vehicle_complaints_analysis.csv'
parquet_path = 'data/integrated/vehicle_complaints_analysis.parquet'

# Read CSV
df = pd.read_csv(csv_path)
print(f"Dataset: {len(df):,} rows × {len(df.columns)} columns")

# Save as Parquet
df.to_parquet(parquet_path, index=False)

# Compare sizes
csv_size = os.path.getsize(csv_path)
parquet_size = os.path.getsize(parquet_path)
reduction = (1 - parquet_size/csv_size) * 100

print(f"\nFile sizes:")
print(f" CSV: {format_size(csv_size)}")
print(f" Parquet: {format_size(parquet_size)}")
print(f" Savings: {reduction:.1f}% smaller")

# Clean up (remove the parquet file)
os.remove(parquet_path)
