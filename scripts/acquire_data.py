import requests
import os
import zipfile  # unzipping EPA file
import json
import pandas as pd  # converting DOE JSON to CSV
from dotenv import load_dotenv  # loading environment variables

load_dotenv()

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

# 3. DOE Alternative Fuel Stations Data (via NREL API)
nrel_api_key = os.getenv('NREL_API_KEY')
if not nrel_api_key:
    print("ERROR: NREL_API_KEY not found in environment variables.")
    print("Please create a .env file with your API key or set it in your environment.")
    print("Sign up at https://developer.nrel.gov/signup/ to get a free API key.")
else:
    nrel_url = f"https://developer.nrel.gov/api/alt-fuel-stations/v1.json?api_key={nrel_api_key}&limit=all"
    nrel_response = requests.get(nrel_url)
    if nrel_response.status_code == 200:
        data = nrel_response.json()
        if 'fuel_stations' in data:
            df = pd.DataFrame(data['fuel_stations'])
            df.to_csv('data/raw/alt_fuel_stations.csv', index=False)
            print(f"Alternative fuel stations data downloaded: {len(df)} stations saved to data/raw/alt_fuel_stations.csv")
        else:
            print("No fuel station data found in API response")
    else:
        print(f"Failed to download alternative fuel stations data: {nrel_response.status_code}")
        print("Fallback: You can manually download from https://afdc.energy.gov/data_download")
