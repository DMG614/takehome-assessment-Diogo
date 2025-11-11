# Data Integration Documentation

## Overview

This document explains the data integration process that joins the cleaned EPA, NHTSA, and DOE datasets to create analysis-ready tables. These integrated datasets provide valuable insights into the relationships between vehicle fuel economy, reliability, and fuel infrastructure.

## Purpose

As an automotive supplier, understanding the connections between vehicle performance, customer complaints, and infrastructure availability is critical for strategic decision-making. The integration layer transforms three independent datasets into actionable intelligence.

## Input Datasets

The integration process uses three cleaned datasets:

1. **EPA Vehicles** (`epa_vehicles_clean.csv`): 19,952 records with fuel economy data
2. **NHTSA Complaints** (`nhtsa_complaints_clean.csv`): 412,704 complaint records
3. **DOE Fuel Stations** (`doe_fuel_stations_clean.csv`): 92,366 alternative fuel stations

## Integrated Datasets (3 Total)

### 1. Vehicle Complaints Analysis (EPA + NHTSA)

**File:** `data/integrated/vehicle_complaints_analysis.csv`

**Join Logic:**
- Joins EPA vehicles with NHTSA complaints on `year`, `make`, and `model`
- Aggregates complaints per vehicle to calculate total complaints, crash/fire incidents, injuries, and deaths
- Vehicles without complaints are included with zero values

**Schema:**
| Column | Type | Description |
|--------|------|-------------|
| year | int | Vehicle model year |
| make | string | Manufacturer name |
| model | string | Vehicle model name |
| VClass | string | EPA vehicle class |
| drive | string | Drivetrain type |
| cylinders | float | Number of cylinders |
| displ | float | Engine displacement (liters) |
| fuelType | string | Primary fuel type |
| city08 | int | City MPG |
| highway08 | int | Highway MPG |
| comb08 | int | Combined MPG |
| co2TailpipeGpm | float | CO2 emissions (grams/mile) |
| total_complaints | int | Total complaints filed |
| crash_incidents | int | Complaints involving crashes |
| fire_incidents | int | Complaints involving fires |
| total_injured | int | Total injuries reported |
| total_deaths | int | Total deaths reported |
| avg_complaint_mileage | float | Average mileage when complaint occurred |
| vehicle_variants | int | Number of variants for this year/make/model |

**Business Questions Answered:**
1. **Do fuel-efficient vehicles have more or fewer complaints?**
   - Compare `comb08` (MPG) against `total_complaints` to identify reliability patterns
   - Analysis: Are manufacturers sacrificing reliability for fuel economy?

2. **Which makes/models have the best MPG-to-complaint ratio?**
   - Calculate complaints per MPG to find optimal vehicles
   - Useful for supplier partnerships and component targeting

3. **Are electric vehicles more reliable than gas vehicles?**
   - Filter by `fuelType` and compare complaint rates
   - Strategic insight for EV component suppliers

4. **Which vehicle classes have the most safety issues?**
   - Group by `VClass` and analyze crash/fire incidents
   - Risk assessment for component suppliers

5. **At what mileage do vehicles typically experience problems?**
   - Analyze `avg_complaint_mileage` by make/model
   - Helps understand component lifecycle and warranty implications



---

### 2. Fuel Infrastructure Analysis (EPA + DOE)

**File:** `data/integrated/fuel_infrastructure_analysis.csv`

**Join Logic:**
- Maps EPA fuel types to DOE fuel type codes (e.g., "Electricity" → "ELEC"), to normalize it
- Aggregates vehicle counts by fuel type and year
- Joins with fuel station counts nationwide
- Calculates vehicles-per-station ratios

**Schema:**
| Column | Type | Description |
|--------|------|-------------|
| year | int | Vehicle model year |
| fuel_type_code | string | DOE fuel type code (ELEC, CNG, E85, etc.) |
| vehicle_count | int | Number of vehicles produced |
| avg_combined_mpg | float | Average combined MPG for this fuel type |
| avg_city_mpg | float | Average city MPG |
| avg_highway_mpg | float | Average highway MPG |
| total_stations | int | Total fuel stations nationwide |
| available_stations | int | Currently available stations |
| vehicles_per_station | float | Ratio of vehicles to stations |

**Business Questions Answered:**
1. **Are there enough alternative fuel stations for alternative fuel vehicles?**
   - Compare `vehicle_count` against `available_stations`
   - Identify infrastructure gaps that may limit vehicle adoption

2. **Which fuel types have the worst infrastructure coverage?**
   - Analyze `vehicles_per_station` ratio
   - High ratios indicate infrastructure bottlenecks

3. **Is infrastructure availability improving over time?**
   - Track station counts across years
   - Assess market readiness for alternative fuel vehicles

4. **Which alternative fuel types offer the best fuel economy?**
   - Compare `avg_combined_mpg` across fuel types
   - Guide component development priorities


---

### 3. Comprehensive Vehicle Analysis (EPA + NHTSA + DOE)

**File:** `data/integrated/comprehensive_vehicle_analysis.csv`

**Join Logic:**
- Combines vehicle complaints analysis (EPA + NHTSA) with fuel infrastructure data (DOE)
- Provides complete view of vehicles, complaints, and station availability
- All columns from vehicle complaints analysis plus nationwide station counts

**Additional Columns:**
| Column | Type | Description |
|--------|------|-------------|
| fuel_type_code | string | DOE fuel type code |
| stations_nationwide | int | Total stations for this fuel type |

**Business Questions Answered:**
1. **Do vehicles with limited fuel infrastructure have more complaints?**
   - Correlate `stations_nationwide` with `total_complaints`
   - Assess infrastructure impact on customer satisfaction

2. **Are alternative fuel vehicles less reliable due to infrastructure gaps?**
   - Compare complaint rates for fuel types with different station availability
   - Guide infrastructure investment decisions

3. **Which vehicle segments offer the best opportunities for suppliers?**
   - Combine fuel economy, reliability, and infrastructure data
   - Identify underserved markets

4. **What is the complete lifecycle view of vehicle performance?**
   - From production (EPA) to usage (NHTSA) to infrastructure (DOE)
   - End-to-end strategic planning


---

## Integration Process

The integration script (`scripts/integrate_data.py`) performs the following steps:

1. **Load cleaned datasets** from `data/processed/`
2. **Normalize join keys** (uppercase make/model names, standardize fuel type codes)
3. **Create aggregations** (sum complaints, count stations, calculate averages)
4. **Perform joins** (left joins to preserve all vehicles, even without complaints)
5. **Calculate metrics** (vehicles per station, complaint rates)
6. **Save integrated datasets** to `data/integrated/`

### Key Design Decisions

**Why left joins instead of inner joins?**
- Preserves vehicles without complaints (important for reliability analysis)
- Shows full picture: some vehicles don't have issues

**Why aggregate complaints before joining?**
- NHTSA has multiple complaints per vehicle
- Aggregation prevents duplicate vehicle records
- Provides summary metrics (total complaints, incidents)

**Why map fuel types?**
- EPA uses descriptive names ("Electricity", "Gasoline or E85")
- DOE uses codes ("ELEC", "E85", "CNG")
- Mapping enables joins across different naming conventions

**Why create multiple integrated datasets instead of one?**
- Different analyses require different granularity
- Smaller datasets are easier to work with
- Supports various business questions without much complexity

---

## Running the Integration

To create the integrated datasets:

```bash
python scripts/integrate_data.py
```

The script will:
- Load all three cleaned datasets
- Create three integrated CSV files in `data/integrated/`
- Print summary statistics for each join

---

## Data Quality Notes

**Missing Joins:**
- Not all EPA vehicles have NHTSA complaints (expected because of newer vehicles or reliable models)
- Some EPA fuel types don't map to DOE codes ("Regular Gasoline" has no alternative fuel stations)
- NHTSA complaints lack geographic data, limiting state-level joins

**Normalization Challenges:**
- Make/model names vary slightly between datasets ("CHEVROLET" vs "Chevrolet")
- Solution: uppercase and strip whitespace before joining

**Data Interpretation:**
- Zero complaints doesn't necessarily mean perfect reliability (could, perhaps, indicate low sales volume)
- High vehicles-per-station ratio may be acceptable for fuel types with home refueling (EVs)

---

## Summary

The data integration layer creates three analytical datasets that answer critical business questions for automotive suppliers:

1. **Vehicle Complaints Analysis** - Which vehicles are reliable and fuel-efficient?
2. **Fuel Infrastructure Analysis** - Is there enough infrastructure for alternative fuel vehicles?
3. **Comprehensive Analysis** - What is the complete picture of vehicle performance and infrastructure?
