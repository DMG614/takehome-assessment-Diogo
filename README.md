# Automotive Data Integration Pipeline

This repository contains a complete data pipeline that integrates vehicle fuel economy data (EPA), safety complaints (NHTSA), and alternative fuel infrastructure (DOE) into analysis-ready datasets. Built for the Bosch Data Engineer assessment.

Author: Diogo Gomes

## Overview

The automotive industry generates data across disconnected systems - government fuel economy databases, safety complaint tracking, and infrastructure registries. This project demonstrates a full ETL pipeline that acquires data from public sources (bulk downloads and APIs), processes and cleans it, integrates across sources, and prepares it for loading into a data warehouse.

The pipeline produces three integrated datasets:
- Vehicle complaints analysis (fuel economy + safety incidents)
- Fuel infrastructure analysis (vehicle adoption + charging/refueling stations)
- Comprehensive vehicle analysis (all sources combined)

## Data Sources Overview

### EPA Fuel Economy Data
The Environmental Protection Agency maintains comprehensive vehicle fuel economy data dating back to 1984. This dataset includes MPG ratings (city, highway, combined), engine specifications (cylinders, displacement), vehicle characteristics (class, drivetrain), CO2 emissions, and fuel types. The data is downloaded as a bulk ZIP file from fueleconomy.gov and covers approximately 45,000 vehicle configurations. For this pipeline, data is filtered to 2010+ to align with modern vehicle coverage in the other sources.

### NHTSA Safety Complaints
The National Highway Traffic Safety Administration tracks consumer complaints about vehicle safety issues, crashes, fires, and injuries. Each complaint includes details like vehicle make/model/year, incident description, mileage, and component failures. The raw data contains individual complaint records (one row per complaint), which are aggregated by vehicle to create summary statistics like total complaints, crash incidents, and fire incidents. Downloaded as bulk ZIP files covering 2020-2024, this data provides the safety signal for identifying problematic vehicles.

### DOE Alternative Fuel Stations
The Department of Energy's Alternative Fuels Data Center maintains a registry of alternative fuel stations across the United States, including EV charging stations, CNG, hydrogen, biodiesel, and E85 locations. Accessed via the NREL API, this dataset provides current station counts by fuel type and location. The limitation is that it only provides a current snapshot. There's no historical data about how many stations existed in previous years, so the same counts are replicated across all years in the integrated analysis.

## Quick Start

### Prerequisites
- Python 3.8+
- NREL API key (for DOE data) - get one at https://developer.nrel.gov/signup/

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd takehome-assessment-Diogo

# Install dependencies
pip install -r requirements.txt

# Create .env file with API key
echo "NREL_API_KEY=your_key_here" > .env
```

### Run the Pipeline

```bash
# Full pipeline (acquire, process, integrate, load)
python run_pipeline.py

# Skip data acquisition (use existing raw data)
python run_pipeline.py --skip-data
```

Output files are created in:
- `data/raw/` - Downloaded datasets
- `data/processed/` - Cleaned datasets
- `data/integrated/` - Final analysis-ready files

## Project Structure

```
takehome-assessment-Diogo/
├── scripts/
│   ├── acquire_data.py           # Download from EPA, NHTSA, DOE sources
│   ├── process_epa.py            # Clean fuel economy data
│   ├── process_nhtsa.py          # Clean safety complaints
│   ├── process_doe.py            # Clean infrastructure data
│   ├── integrate_data.py         # Join datasets, create analysis tables
│   ├── load_data.py              # Generate Delta Lake SQL (simulated)
│   ├── validate_data.py          # Data quality checks
│   └── parquet_comparison.py     # Format efficiency demo
├── data/
│   ├── raw/                      # Downloaded files
│   ├── processed/                # Cleaned files
│   └── integrated/               # Final datasets
├── docs/
│   ├── data_acquisition.md
│   ├── data_integration.md
│   ├── data_loading_strategy.md
│   ├── data_schemas.md
│   ├── processing_strategy.md
│   ├── processing_scripts_documentation.md
│   ├── format_decision.md
│   └── challenges_faced.md
├── requirements.txt
└── run_pipeline.py               # Main entry point
```

## Pipeline Stages

### 1. Data Acquisition
Downloads data from three public sources:
- **EPA**: Vehicle fuel economy (1984-2025) - bulk ZIP download from fueleconomy.gov
- **NHTSA**: Safety complaints (2020-2024) - bulk ZIP download from nhtsa.gov
- **DOE**: Alternative fuel stations - NREL API (requires API key)

See [data_acquisition.md](docs/data_acquisition.md) for details.

### 2. Data Processing
Cleans and standardizes each source:
- EPA: Filter relevant columns, handle electric vehicles, normalize fuel types
- NHTSA: Aggregate complaints by vehicle, parse incident types
- DOE: Group stations by fuel type and year

### 3. Data Integration
Joins datasets on `year`, `make`, `model`:
- `vehicle_complaints_analysis.csv` - EPA + NHTSA
- `fuel_infrastructure_analysis.csv` - EPA + DOE (aggregated by fuel type)
- `comprehensive_vehicle_analysis.csv` - All three sources

### 4. Data Loading
Generates SQL statements for Databricks Delta Lake (simulated):
- Creates tables with schema
- Uses `COPY INTO` for CSV ingestion
- Implements full-refresh loading pattern

See [data_loading_strategy.md](docs/data_loading_strategy.md) for details.

### 5. Automation
Proposes Azure Data Factory orchestration for production deployment with scheduled triggers, monitoring, and error handling.

See [automation_strategy.md](docs/automation_strategy.md) for details.

## Data Sources

1. **EPA Fuel Economy Data**
   Source: https://www.fueleconomy.gov/feg/download.shtml (bulk ZIP download)
   Coverage: 1984-2025, ~45K vehicles

2. **NHTSA Safety Complaints**
   Source: https://static.nhtsa.gov/odi/ffdd/cmpl/ (bulk ZIP download)
   Coverage: Safety incidents, recalls, investigations (2020-2024)

3. **DOE Alternative Fuel Stations**
   API: https://developer.nrel.gov/docs/transportation/alt-fuel-stations-v1/
   Coverage: EV charging, CNG, hydrogen stations (US)

## Output Datasets

### vehicle_complaints_analysis.csv
Combines EPA fuel economy data with NHTSA safety complaints. Each row represents a vehicle-fuel combination (dual-fuel vehicles like plug-in hybrids appear twice - once for each fuel type). Enables analysis of relationships between vehicle characteristics and safety issues. ~21,307 rows.

Key columns: `year`, `make`, `model`, `fuel_used`, `fuel_rank`, `comb08` (MPG), `total_complaints`, `crash_incidents`, `fire_incidents`

### fuel_infrastructure_analysis.csv
Aggregates vehicle-fuel combinations by fuel type and year, joining with DOE alternative fuel station counts. Answers infrastructure availability questions like whether there are enough EV charging stations for electric vehicles. Dual-fuel vehicles (like plug-in hybrids) are counted in each fuel type category they support, providing accurate infrastructure demand estimates. ~43 rows.

Key columns: `year`, `fuel_type_code`, `vehicle_count`, `total_stations`, `vehicles_per_station`

### comprehensive_vehicle_analysis.csv
Combines all three data sources, providing the most complete view with fuel economy, safety complaints, and infrastructure availability. Each row represents a vehicle-fuel combination. Best for exploratory analysis, though DOE station counts are current snapshots replicated across years. ~21,307 rows.

Key columns: All columns from vehicle_complaints_analysis plus `stations_nationwide`, `fuel_type_code`

## Documentation

- [data_acquisition.md](docs/data_acquisition.md) - Data source acquisition strategies
- [processing_strategy.md](docs/processing_strategy.md) - Processing decisions and transformations
- [data_integration.md](docs/data_integration.md) - Dataset integration approach
- [data_loading_strategy.md](docs/data_loading_strategy.md) - Delta Lake loading approach
- [automation_strategy.md](docs/automation_strategy.md) - Azure Data Factory orchestration
- [format_decision.md](docs/format_decision.md) - CSV vs Parquet tradeoffs
- [challenges_faced.md](docs/challenges_faced.md) - Issues encountered and solutions

## Additional Scripts

### validate_data.py
Runs data quality checks on integrated datasets:
```bash
python scripts/validate_data.py
```

Checks:
- Required columns exist
- No nulls in key fields
- Year ranges are reasonable (2010-2025)
- MPG values are positive
- Minimum row counts met

### parquet_comparison.py
Demonstrates Parquet format efficiency:
```bash
python scripts/parquet_comparison.py
```

Shows file size comparison (CSV: 2.36 MB, Parquet: 0.25 MB = 90% reduction).

See [format_decision.md](docs/format_decision.md) for why CSV was chosen for this assessment.

## Notes

- **DOE API Key**: Required for alternative fuel stations data. Create `.env` file with `NREL_API_KEY=your_key`
- **Delta Lake Loading**: `load_data.py` generates SQL but doesn't connect to Databricks (simulated for assessment)
- **Data Refresh**: EPA and NHTSA data updates annually. DOE stations data updates quarterly.
- **Format Choice**: CSV used for reviewability. Production would use Parquet/Delta Lake. See [format_decision.md](docs/format_decision.md).

## Testing

Run validation checks:
```bash
python scripts/validate_data.py
```

Expected output:
```
data/integrated/vehicle_complaints_analysis.csv: 21,307 rows
data/integrated/fuel_infrastructure_analysis.csv: 43 rows
data/integrated/comprehensive_vehicle_analysis.csv: 21,307 rows

Data quality checks:
All checks passed

Validation complete
```

**Note**: Row counts reflect vehicle-fuel combinations. Dual-fuel vehicles (like plug-in hybrids) appear twice.

## Known Issues

See [challenges_faced.md](docs/challenges_faced.md) for issues encountered and their solutions.
