"""
Data Integration Script

This script creates integrated datasets by joining the cleaned EPA, NHTSA, and DOE data.
These joins provide analytical value for understanding relationships between vehicle
fuel economy, reliability (complaints), and fuel infrastructure.

Input files (from data/processed/):
- epa_vehicles_clean.csv
- nhtsa_complaints_clean.csv
- doe_fuel_stations_clean.csv

Output files (to data/integrated/):
- vehicle_complaints_analysis.csv (EPA + NHTSA)
- fuel_infrastructure_analysis.csv (EPA + DOE)
- comprehensive_vehicle_analysis.csv (EPA + NHTSA + DOE)
"""

import pandas as pd
import os

def load_cleaned_data():
    """Load the three cleaned datasets"""
    print("Loading cleaned datasets")

    epa_df = pd.read_csv('data/processed/epa_vehicles_clean.csv')
    nhtsa_df = pd.read_csv('data/processed/nhtsa_complaints_clean.csv')
    doe_df = pd.read_csv('data/processed/doe_fuel_stations_clean.csv')

    print(f"EPA vehicles: {len(epa_df):,} records")
    print(f"NHTSA complaints: {len(nhtsa_df):,} records")
    print(f"DOE fuel stations: {len(doe_df):,} records")

    return epa_df, nhtsa_df, doe_df


def create_vehicle_complaints_analysis(epa_df, nhtsa_df):
    """
    Join EPA vehicles with NHTSA complaints to analyze fuel economy vs reliability.

    This join answers questions like:
    - Do fuel-efficient vehicles have more or fewer complaints?
    - Which makes/models have the best MPG to complaint ratio?
    - Are certain vehicle types more reliable?
    """
    print("\nCreating Vehicle Complaints Analysis")

    # Normalize make names for better matching (uppercase, strip whitespace)
    epa_df['make_norm'] = epa_df['make'].str.upper().str.strip()
    epa_df['model_norm'] = epa_df['model'].str.upper().str.strip()
    nhtsa_df['make_norm'] = nhtsa_df['MAKETXT'].str.upper().str.strip()
    nhtsa_df['model_norm'] = nhtsa_df['MODELTXT'].str.upper().str.strip()

    # Aggregate complaints by vehicle (year, make, model)
    complaints_summary = nhtsa_df.groupby(['YEARTXT', 'make_norm', 'model_norm']).agg({
        'CMPLID': 'count',  # Total complaints
        'CRASH': lambda x: (x == 'Y').sum(),  # Crash incidents
        'FIRE': lambda x: (x == 'Y').sum(),  # Fire incidents
        'INJURED': 'sum',  # Total injuries
        'DEATHS': 'sum',  # Total deaths
        'MILEAGE': 'mean'  # Average mileage when complaint occurred
    }).reset_index()

    complaints_summary.columns = ['year', 'make_norm', 'model_norm', 'total_complaints',
                                   'crash_incidents', 'fire_incidents', 'total_injured',
                                   'total_deaths', 'avg_complaint_mileage']

    print(f"Aggregated complaints into {len(complaints_summary):,} unique vehicle groups")

    # Join with EPA data
    joined_df = epa_df.merge(
        complaints_summary,
        #left_on=['year', 'make_norm', 'model_norm'],
        #right_on=['year', 'make_norm', 'model_norm'],
        on=['year', 'make_norm', 'model_norm'],
        how='left'
    )

    # Fill NaN for vehicles with no complaints
    complaint_cols = ['total_complaints', 'crash_incidents', 'fire_incidents',
                      'total_injured', 'total_deaths', 'avg_complaint_mileage']
    joined_df[complaint_cols] = joined_df[complaint_cols].fillna(0)

    # Select relevant columns for analysis
    analysis_df = joined_df[[
        'year', 'make', 'model', 'VClass', 'drive', 'cylinders', 'displ',
        'fuelType', 'city08', 'highway08', 'comb08', 'co2TailpipeGpm',
        'total_complaints', 'crash_incidents', 'fire_incidents',
        'total_injured', 'total_deaths', 'avg_complaint_mileage'
    ]]

    # Calculate complaints per vehicle metric (normalized by how many of that model exist)
    # Group by year/make/model to get vehicle count
    vehicle_counts = analysis_df.groupby(['year', 'make', 'model']).size().reset_index(name='vehicle_variants')
    analysis_df = analysis_df.merge(
                            vehicle_counts, 
                            on=['year', 'make', 'model'], 
                            how='left')

    # Remove the normalized columns used for joining
    analysis_df = analysis_df.drop_duplicates()

    print(f"Created vehicle complaints analysis with {len(analysis_df):,} records")
    print(f"Vehicles with complaints: {(analysis_df['total_complaints'] > 0).sum():,}")
    print(f"Vehicles without complaints: {(analysis_df['total_complaints'] == 0).sum():,}")

    return analysis_df


def create_fuel_infrastructure_analysis(epa_df, doe_df):
    """
    Join EPA vehicles with DOE fuel stations to analyze infrastructure availability.

    This join answers questions like:
    - Are there enough fuel stations for alternative fuel vehicles?
    - Which states have the best infrastructure for EVs, hybrids, etc?
    - Is there a mismatch between vehicle production and station availability?
    """
    print("\nCreating Fuel Infrastructure Analysis")

    # Map EPA fuel types to DOE fuel type codes
    # EPA uses descriptive names, DOE uses codes
    # In this map key is the EPA descriptive names and the value is the DOE fuel type code
    # This needs to be made because in EPA the fuel types are descriptive and in the DOE they are codes
    fuel_type_mapping = {
        'Electricity': 'ELEC',
        'Gasoline or E85': 'E85',
        'CNG': 'CNG',
        'Diesel': 'BD',  # Biodiesel
        'Hydrogen': 'HY',
        'Gasoline or natural gas': 'CNG',
        'LPG': 'LPG',
        'LNG': 'LNG'
    }

    # Create mapped fuel type for EPA data
    epa_df['fuel_type_code'] = epa_df['fuelType1'].map(fuel_type_mapping)

    # Count vehicles by fuel type and year
    vehicle_counts = epa_df.groupby(['year', 'fuel_type_code']).agg({
        'id': 'count',
        'comb08': 'mean',
        'city08': 'mean',
        'highway08': 'mean'
    }).reset_index()

    vehicle_counts.columns = ['year', 'fuel_type_code', 'vehicle_count',
                               'avg_combined_mpg', 'avg_city_mpg', 'avg_highway_mpg']

    # Count fuel stations by type and state
    station_counts = doe_df.groupby(['fuel_type_code', 'state']).agg({
        'id': 'count',
        'status_code': lambda x: (x == 'E').sum()  # Available stations
    }).reset_index()

    station_counts.columns = ['fuel_type_code', 'state', 'total_stations', 'available_stations']

    # Calculate total stations by fuel type (across all states)
    total_stations_by_fuel = station_counts.groupby('fuel_type_code').agg({
        'total_stations': 'sum',
        'available_stations': 'sum'
    }).reset_index()

    # Join vehicles with station availability
    infrastructure_df = vehicle_counts.merge(
        total_stations_by_fuel,
        on='fuel_type_code',
        how='left'
    )

    # Fill NaN for fuel types with no stations
    infrastructure_df[['total_stations', 'available_stations']] = \
        infrastructure_df[['total_stations', 'available_stations']].fillna(0)

    # Calculate vehicles per station ratio
    infrastructure_df['vehicles_per_station'] = \
        infrastructure_df['vehicle_count'] / infrastructure_df['total_stations'].replace(0, 1)

    # Round numeric columns
    infrastructure_df['avg_combined_mpg'] = infrastructure_df['avg_combined_mpg'].round(1)
    infrastructure_df['avg_city_mpg'] = infrastructure_df['avg_city_mpg'].round(1)
    infrastructure_df['avg_highway_mpg'] = infrastructure_df['avg_highway_mpg'].round(1)
    infrastructure_df['vehicles_per_station'] = infrastructure_df['vehicles_per_station'].round(1)

    print(f"Created fuel infrastructure analysis with {len(infrastructure_df):,} records")
    print(f"Fuel types analyzed: {infrastructure_df['fuel_type_code'].nunique()}")

    return infrastructure_df


def create_comprehensive_analysis(epa_df, nhtsa_df, doe_df):
    """
    Create a comprehensive dataset joining all three sources.

    This provides a complete view for end-to-end analysis of vehicles,
    complaints, and infrastructure.
    """
    print("\nComprehensive Vehicle Analysis")

    # Start with vehicle complaints analysis (EPA + NHTSA)
    base_df = create_vehicle_complaints_analysis(epa_df.copy(), nhtsa_df.copy())

    # Add fuel infrastructure metrics
    # Map fuel types
    fuel_type_mapping = {
        'Electricity': 'ELEC',
        'Gasoline or E85': 'E85',
        'CNG': 'CNG',
        'Diesel': 'BD',
        'Hydrogen': 'HY',
        'Gasoline or natural gas': 'CNG',
        'LPG': 'LPG',
        'LNG': 'LNG'
    }

    base_df['fuel_type_code'] = base_df['fuelType'].map(fuel_type_mapping)

    # Get station counts by fuel type
    station_counts = doe_df.groupby('fuel_type_code').agg({
        'id': 'count'
    }).reset_index()
    station_counts.columns = ['fuel_type_code', 'stations_nationwide']

    # Join with infrastructure data
    comprehensive_df = base_df.merge(
        station_counts,
        on='fuel_type_code',
        how='left'
    )

    comprehensive_df['stations_nationwide'] = comprehensive_df['stations_nationwide'].fillna(0)

    print(f"Created comprehensive analysis with {len(comprehensive_df):,} records")

    return comprehensive_df


def main():
    print("Data Integration Script")

    os.makedirs('data/integrated', exist_ok=True)

    # Load cleaned data
    epa_df, nhtsa_df, doe_df = load_cleaned_data()

    # Create integrated datasets

    # 1. Vehicle Complaints Analysis (EPA + NHTSA)
    vehicle_complaints = create_vehicle_complaints_analysis(epa_df.copy(), nhtsa_df.copy())
    vehicle_complaints.to_csv('data/integrated/vehicle_complaints_analysis.csv', index=False)
    print(f"Saved: data/integrated/vehicle_complaints_analysis.csv")

    # 2. Fuel Infrastructure Analysis (EPA + DOE)
    fuel_infrastructure = create_fuel_infrastructure_analysis(epa_df.copy(), doe_df.copy())
    fuel_infrastructure.to_csv('data/integrated/fuel_infrastructure_analysis.csv', index=False)
    print(f"Saved: data/integrated/fuel_infrastructure_analysis.csv")

    # 3. Comprehensive Analysis (EPA + NHTSA + DOE)
    comprehensive = create_comprehensive_analysis(epa_df.copy(), nhtsa_df.copy(), doe_df.copy())
    comprehensive.to_csv('data/integrated/comprehensive_vehicle_analysis.csv', index=False)
    print(f"Saved: data/integrated/comprehensive_vehicle_analysis.csv")

    print("Integration Done")

    print("\nGenerated 3 integrated datasets:")
    print("1. vehicle_complaints_analysis.csv - Fuel economy vs reliability")
    print("2. fuel_infrastructure_analysis.csv - Vehicle production vs station availability")
    print("3. comprehensive_vehicle_analysis.csv - Complete integrated view")


if __name__ == '__main__':
    main()
