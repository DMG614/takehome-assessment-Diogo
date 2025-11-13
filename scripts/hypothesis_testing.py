"""
Hypothesis Testing - Automotive Data Integration

Tests business hypotheses using the integrated datasets.
"""

import pandas as pd
import numpy as np

complaints_df = pd.read_csv('data/integrated/vehicle_complaints_analysis.csv')
infrastructure_df = pd.read_csv('data/integrated/fuel_infrastructure_analysis.csv')
comprehensive_df = pd.read_csv('data/integrated/comprehensive_vehicle_analysis.csv')

print("Hypothesis Testing - Automotive Data Analysis\n")

# H1: Are efficient vehicles more reliable?
print("1. Do efficient vehicles have fewer complaints?")

high_mpg = complaints_df[complaints_df['comb08'] > 30]
low_mpg = complaints_df[complaints_df['comb08'] <= 30]

print(f"   High MPG vehicles (>30): {high_mpg['total_complaints'].mean():.1f} avg complaints")
print(f"   Low MPG vehicles (<=30): {low_mpg['total_complaints'].mean():.1f} avg complaints")

if high_mpg['total_complaints'].mean() < low_mpg['total_complaints'].mean():
    diff = low_mpg['total_complaints'].mean() - high_mpg['total_complaints'].mean()
    print(f"   Result: Efficient vehicles have {diff:.1f} fewer complaints on average\n")
else:
    print("   Result: No clear correlation between efficiency and reliability\n")

# H2: Which brands have the highest complaint rates?
print("2. Which brands have the most safety issues?")

brand_complaints = complaints_df.groupby('make').agg({
    'total_complaints': 'sum',
    'crash_incidents': 'sum',
    'fire_incidents': 'sum',
    'year': 'count'
}).rename(columns={'year': 'vehicle_count'})

brand_complaints['complaints_per_vehicle'] = (
    brand_complaints['total_complaints'] / brand_complaints['vehicle_count']
)

brands_with_data = brand_complaints[brand_complaints['vehicle_count'] > 50].copy()
top_problematic = brands_with_data.nlargest(5, 'complaints_per_vehicle')

print("   Top 5 brands by complaints per vehicle (min 50 models):")
for make, row in top_problematic.iterrows():
    print(f"   {make:20s} {row['complaints_per_vehicle']:6.1f} complaints/vehicle "
          f"({row['crash_incidents']:.0f} crashes, {row['fire_incidents']:.0f} fires)")
    
# H3: Are EVs reporting fewer issues?
print("3. Do electric vehicles have fewer complaints than gas vehicles?")

evs = complaints_df[complaints_df['fuel_used'].str.contains('Electricity', case=False, na=False)]
gas = complaints_df[complaints_df['fuel_used'].str.contains('Gasoline', case=False, na=False)]

ev_avg = evs['total_complaints'].mean()
gas_avg = gas['total_complaints'].mean()

print(f"   Electric vehicles: {ev_avg:.1f} avg complaints ({len(evs):,} vehicle-fuel combos)")
print(f"   Gasoline vehicles: {gas_avg:.1f} avg complaints ({len(gas):,} vehicle-fuel combos)")

if ev_avg < gas_avg:
    pct_diff = ((gas_avg - ev_avg) / gas_avg * 100)
    print(f"   Result: EVs have {pct_diff:.1f}% fewer complaints\n")
else:
    print("   Result: EVs do not have significantly fewer complaints\n")

# H4: Which fuel types are infrastructure-constrained?
print("4. Which fuel types lack adequate infrastructure?")
print("   (Using 10 stations per 1,000 vehicles as minimum threshold)")

infra_2024 = infrastructure_df[infrastructure_df['year'] == 2024].copy()
infra_2024['stations_per_1000_vehicles'] = (
    infra_2024['total_stations'] / infra_2024['vehicle_count'] * 1000
)

print("\n   Stations per 1,000 vehicles by fuel type (2024):")
for _, row in infra_2024.sort_values('stations_per_1000_vehicles').iterrows():
    status = "constrained" if row['stations_per_1000_vehicles'] < 10 else "adequate"
    print(f"   {row['fuel_type_code']:8s} {row['stations_per_1000_vehicles']:6.1f} stations/1k vehicles "
          f"({row['total_stations']:,} stations, {row['vehicle_count']:,} vehicles) - {status}")

constrained = infra_2024[infra_2024['stations_per_1000_vehicles'] < 10]
if len(constrained) > 0:
    print(f"\n   Infrastructure gaps identified: {', '.join(constrained['fuel_type_code'].values)}")
else:
    print("\n   All fuel types have adequate infrastructure coverage")

# H5: Do infrastructure gaps correlate with more complaints?
print("5. Do vehicles with poor infrastructure have more complaints?")

high_infra = comprehensive_df[comprehensive_df['stations_nationwide'] > 10000]
low_infra = comprehensive_df[comprehensive_df['stations_nationwide'] <= 10000]

high_avg = high_infra['total_complaints'].mean()
low_avg = low_infra['total_complaints'].mean()

print(f"   Good infrastructure (>10k stations): {high_avg:.1f} avg complaints")
print(f"   Poor infrastructure (<=10k stations): {low_avg:.1f} avg complaints")

if low_avg > high_avg:
    pct_diff = ((low_avg - high_avg) / high_avg * 100)
    print(f"   Result: Poor infrastructure correlates with {pct_diff:.1f}% more complaints\n")
else:
    print("   Result: No clear correlation between infrastructure and complaints\n")

# BONUS: Best overall segment
print("6. Which vehicle classes perform best overall?")

segment_analysis = comprehensive_df.groupby('VClass').agg({
    'comb08': 'mean',
    'total_complaints': 'mean',
    'year': 'count'
}).rename(columns={'year': 'count'})

segments_with_data = segment_analysis[segment_analysis['count'] > 100].copy()

print(f"\n   Top 5 most efficient vehicle classes (min 100 models):")
top_efficient = segments_with_data.nlargest(5, 'comb08')
for vclass, row in top_efficient.iterrows():
    print(f"   {vclass:35s} {row['comb08']:5.1f} MPG avg, {row['total_complaints']:5.1f} complaints avg")

print(f"\n   Top 5 most reliable vehicle classes (fewest complaints, min 100 models):")
top_reliable = segments_with_data.nsmallest(5, 'total_complaints')
for vclass, row in top_reliable.iterrows():
    print(f"   {vclass:35s} {row['total_complaints']:5.1f} complaints avg, {row['comb08']:5.1f} MPG avg")

