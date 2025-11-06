import requests
import os
import zipfile  # For unzipping EPA file
import json
import pandas as pd  # For converting DOE JSON to CSV; pip install pandas if needed

# Create directories if they don't exist
os.makedirs('data/raw', exist_ok=True)

# 1. EPA Fuel Economy Data (Comprehensive CSV in ZIP)
epa_url = "https://www.fueleconomy.gov/feg/epadata/vehicles.csv.zip"
epa_response = requests.get(epa_url)
if epa_response.status_code == 200:
    with open('data/raw/vehicles.zip', 'wb') as f:
        f.write(epa_response.content)
    # Unzip it
    with zipfile.ZipFile('data/raw/vehicles.zip', 'r') as zip_ref:
        zip_ref.extractall('data/raw')
    print("EPA data downloaded and unzipped to data/raw/vehicles.csv")
else:
    print(f"Failed to download EPA data: {epa_response.status_code}")

# 2. NHTSA Vehicle Complaints Data (Recent 5-year ZIP from nhtsa.gov)
nhtsa_url = "https://static.nhtsa.gov/odi/ffdd/cmpl/COMPLAINTS_RECEIVED_2020-2024.zip"
nhtsa_response = requests.get(nhtsa_url)
if nhtsa_response.status_code == 200:
    with open('data/raw/complaints_2020-2024.zip', 'wb') as f:
        f.write(nhtsa_response.content)
    # Unzip it (assumes it contains CSVs or flat files)
    with zipfile.ZipFile('data/raw/complaints_2020-2024.zip', 'r') as zip_ref:
        zip_ref.extractall('data/raw')
    print("NHTSA complaints data downloaded and unzipped to data/raw/")
else:
    print(f"Failed to download NHTSA data: {nhtsa_response.status_code}")