"""
Run the complete data pipeline: acquire → process → integrate → load

Usage:
    python run_pipeline.py              # Full pipeline
    python run_pipeline.py --skip-data  # Skip acquisition, use existing data
"""

import sys
import subprocess
import os
from pathlib import Path


def run(script):
    """Run a script, return True if successful."""
    try:
        subprocess.run([sys.executable, script], check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"\nFailed at: {script}")
        return False


# Quick dependency check
try:
    import pandas
    import requests
    import pyarrow
except ImportError as e:
    print(f"\nMissing package: {e.name}")
    print("Run: pip install -r requirements.txt\n")
    sys.exit(1)

# Create directories
for d in ['data/raw', 'data/processed', 'data/integrated']:
    Path(d).mkdir(parents=True, exist_ok=True)

# Check .env (warning only)
if not os.path.exists('.env'):
    print("\nNote: No .env file found (needed for DOE data acquisition)")
    print("Create .env with: NREL_API_KEY=your_key\n")

# Build pipeline
skip_data = '--skip-data' in sys.argv
scripts = []

if not skip_data:
    scripts.append('scripts/acquire_data.py')

scripts += [
    'scripts/process_epa.py',
    'scripts/process_nhtsa.py',
    'scripts/process_doe.py',
    'scripts/integrate_data.py',
    'scripts/load_data.py'
]

# Run it
print(f"\nRunning {len(scripts)} scripts\n")

for script in scripts:
    if not run(script):
        print("\nPipeline failed.\n")
        sys.exit(1)

print("Done")
print("\nFiles created:")
print("  data/raw/        - 3 raw datasets")
print("  data/processed/  - 3 cleaned datasets")
print("  data/integrated/ - 3 integrated datasets\n")
