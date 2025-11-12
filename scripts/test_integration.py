"""
Integration Testing Script

This script tests the integrated datasets created by integrate_data.py.
It loads each of the 3 integrated datasets and displays key statistics
and sample data to verify the joins worked correctly.
"""

import pandas as pd
import os


def test_vehicle_complaints_analysis():
    """Test the vehicle complaints analysis dataset"""
    print("Test 1: Vehicle Complaints Analysis (EPA + NHTSA)")

    file_path = 'data/integrated/vehicle_complaints_analysis.csv'

    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found")
        return

    df = pd.read_csv(file_path)
    print(f"\nTotal records: {len(df):,}")
    print(f"Columns: {len(df.columns)}")

    # Basic statistics
    vehicles_with_complaints = (df['total_complaints'] > 0).sum()
    vehicles_without_complaints = (df['total_complaints'] == 0).sum()

    print(f"\nVehicles with complaints: {vehicles_with_complaints:,} ({vehicles_with_complaints/len(df)*100:.1f}% of total values)")
    print(f"Vehicles without complaints: {vehicles_without_complaints:,} ({vehicles_without_complaints/len(df)*100:.1f}% of total values)")

    print(f"\nTotal complaints across all vehicles: {df['total_complaints'].sum():,.0f}")
    print(f"Total crash incidents: {df['crash_incidents'].sum():,.0f}")
    print(f"Total fire incidents: {df['fire_incidents'].sum():,.0f}")
    print(f"Total injuries: {df['total_injured'].sum():,.0f}")
    print(f"Total deaths: {df['total_deaths'].sum():,.0f}")

    # Show top 10 vehicles with most complaints
    print("\nTop 10 Vehicles with Most Complaints:")
    top_complaints = df[df['total_complaints'] > 0].nlargest(10, 'total_complaints')
    print(top_complaints[['year', 'make', 'model', 'fuel_used', 'fuel_rank', 'comb08', 'total_complaints',
                          'crash_incidents', 'fire_incidents']].to_string(index=False))

    # Show vehicles with best MPG and zero complaints
    print("\nTop 10 Most Fuel-Efficient Vehicles with Zero Complaints:")
    reliable_efficient = df[df['total_complaints'] == 0].nlargest(10, 'comb08')
    print(reliable_efficient[['year', 'make', 'model', 'fuel_used', 'fuel_rank', 'comb08', 'city08',
                               'highway08']].to_string(index=False))

    print("\nVehicle Complaints Analysis tests complete")


def test_fuel_infrastructure_analysis():
    """Test the fuel infrastructure analysis dataset"""
    print("Test 2: Fuel Infrastructure Analysis (EPA + DOE)")

    file_path = 'data/integrated/fuel_infrastructure_analysis.csv'

    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found")
        return

    df = pd.read_csv(file_path)

    print(f"\nTotal records: {len(df):,}")
    print(f"Unique fuel types: {df['fuel_type_code'].nunique()}")
    print(f"Years covered: {df['year'].min()} to {df['year'].max()}") # as explained before, starts in 2010.

    # Summary by fuel type
    print("\nInfrastructure Summary by Fuel Type:")
    fuel_summary = df.groupby('fuel_type_code').agg({
        'vehicle_count': 'sum',
        'total_stations': 'first',
        'available_stations': 'first',
        'avg_combined_mpg': 'mean'
    }).round(1)
    fuel_summary['vehicles_per_station'] = (fuel_summary['vehicle_count'] /
                                             fuel_summary['total_stations'].replace(0, 1)).round(1)
    print(fuel_summary.to_string())

    # Show worst infrastructure gaps
    print("\nYears with Worst Infrastructure Coverage (highest vehicles per station):")
    worst_coverage = df.nlargest(10, 'vehicles_per_station')
    print(worst_coverage[['year', 'fuel_type_code', 'vehicle_count', 'total_stations',
                          'vehicles_per_station']].to_string(index=False))

    # Show best infrastructure
    print("\nYears with Best Infrastructure Coverage (lowest vehicles per station):")
    # Filter out zero vehicle counts
    best_coverage = df[df['vehicle_count'] > 0].nsmallest(10, 'vehicles_per_station')
    print(best_coverage[['year', 'fuel_type_code', 'vehicle_count', 'total_stations',
                         'vehicles_per_station', 'avg_combined_mpg']].to_string(index=False))

    print("\nFuel Infrastructure Analysis tests complete")


def test_comprehensive_analysis():
    """Test the comprehensive vehicle analysis dataset"""
    print("Test 3: Comprehensive Vehicle Analysis (EPA + NHTSA + DOE)")

    file_path = 'data/integrated/comprehensive_vehicle_analysis.csv'

    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found")
        return

    df = pd.read_csv(file_path)

    print(f"\nTotal records: {len(df):,}")
    print(f"Columns: {len(df.columns)}")

    # Show vehicles with good MPG, few complaints, and good infrastructure
    # Assumption -> best overall comb08 > 35, total_complaints < 10 and stations_nationwide > 1000
    print("\nBest Overall Vehicles (High MPG, Low Complaints, Good Infrastructure):")
    best_overall = df[
        (df['comb08'] > 35) &
        (df['total_complaints'] < 10) &
        (df['stations_nationwide'] > 1000)
    ].nlargest(10, 'comb08')

    if len(best_overall) > 0:
        print(best_overall[['year', 'make', 'model', 'fuel_used', 'fuel_rank', 'comb08', 'total_complaints',
                            'stations_nationwide']].to_string(index=False))
    else:
        print("No vehicles meet all criteria (MPG>35, complaints<10, stations>1000)")
        print("\nRelaxing criteria to MPG>30, complaints<50, stations>500:")
        best_overall = df[
            (df['comb08'] > 30) &
            (df['total_complaints'] < 50) &
            (df['stations_nationwide'] > 500)
        ].nlargest(10, 'comb08')
        print(best_overall[['year', 'make', 'model', 'fuel_used', 'fuel_rank', 'comb08', 'total_complaints',
                            'stations_nationwide']].to_string(index=False))

    # Show infrastructure gaps for complained vehicles
    print("\nVehicles with Many Complaints and Poor Infrastructure:")
    problem_vehicles = df[
        (df['total_complaints'] > 100) &
        (df['stations_nationwide'] < 5000)
    ].drop_duplicates(subset=['year', 'make', 'model']).nlargest(10, 'total_complaints')

    if len(problem_vehicles) > 0:
        print(problem_vehicles[['year', 'make', 'model', 'fuel_used', 'fuel_rank', 'total_complaints',
                                'crash_incidents', 'stations_nationwide']].to_string(index=False))
    else:
        print("No vehicles have complaints>100 with stations<5000")

    print("\nComprehensive Vehicle Analysis tests complete")


def main():
    print("Integration Testing Script")
    print("Testing all 3 integrated datasets")

    # Check if integration has been run
    if not os.path.exists('data/integrated'):
        print("\nError: data/integrated/ directory not found!")
        print("Please run 'python scripts/integrate_data.py' first")
        return

    # Run all tests
    test_vehicle_complaints_analysis()
    test_fuel_infrastructure_analysis()
    test_comprehensive_analysis()

    print("\nIntegrated datasets are ready for analysis and loading.")


if __name__ == '__main__':
    main()
