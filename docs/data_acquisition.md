# Data Acquisition Documentation

## Overview

The [acquire_data.py](../scripts/acquire_data.py) script automates the download of three public automotive datasets from U.S. government sources. These datasets form the foundation for analyzing trends in vehicle efficiency, safety issues, and alternative fuel infrastructure—all relevant to understanding the automotive industry's evolution toward sustainable mobility.

The script is built in Python and handles HTTP downloads, file extraction, API integration, and JSON-to-CSV conversion. Each data source is independent, so if one fails, the others continue running. Basic error handling ensures failures are reported clearly rather than causing silent errors.

---

## Why Different Methods for Different Sources?

A common question: why use an API for the alternative fuel stations but direct downloads for EPA and NHTSA?

**Short answer:** Each source was handled with the simplest method that enables full automation.

- **EPA & NHTSA**: Both provide direct download links to bulk files—no form required, no authentication needed. A simple HTTP GET request retrieves the entire dataset. Using their APIs would add unnecessary complexity (pagination, rate limits, authentication) for no benefit.

- **DOE Alternative Fuel Stations**: The assessment-provided link requires filling out a web form with contact information before each download. This manual step cannot be automated. The NREL API provides the same data programmatically, making it the only viable option for a truly automated pipeline.

The principle: **use the simplest tool that solves the automation requirement**. When bulk downloads work, use them. When only an API enables automation, use that.

---

## Data Sources

### 1. EPA Vehicle Fuel Economy Data

**Source:** https://www.fueleconomy.gov/feg/epadata/vehicles.csv.zip
**Output:** `data/raw/vehicles.csv` (~49,000 vehicles, 1984–present, 84 columns)

This dataset contains comprehensive fuel economy specifications for vehicles sold in the U.S. since 1984. Key fields include make, model, year, city/highway/combined MPG, CO2 emissions, engine displacement, fuel type, and transmission type.

**Why This Approach:**
- The EPA provides a bulk download file that delivers the entire dataset in one request
<!-- - The ZIP format reduces download size from ~20MB to ~2MB -->
- No API key or authentication required
- Single download is more reliable than paginated API calls

**Implementation:**
```python
requests.get(url) → save ZIP → extract with zipfile module → vehicles.csv
```

The script checks the HTTP status code before proceeding. If the download fails, it prints an error and moves to the next source without crashing.

**Alternative Approaches Considered:**
- **EPA Web Services API**: Available at https://fueleconomy.gov/feg/ws/, but requires multiple paginated requests to fetch 49,000 records. The bulk file is simpler and faster.
- **Manual Download**: Could work locally, but defeats the automation requirement.

---

### 2. NHTSA Vehicle Complaints Data

**Source:** https://static.nhtsa.gov/odi/ffdd/cmpl/COMPLAINTS_RECEIVED_2020-2024.zip
**Output:** `data/raw/COMPLAINTS_RECEIVED_2020-2024.txt` (311MB uncompressed, tab-delimited)

This dataset contains consumer complaints about vehicle defects and safety issues filed with NHTSA from 2020 to 2024. It includes fields like complaint date, vehicle year/make/model, component that failed, description of the problem, and whether injuries or crashes occurred.

**Why This Approach:**
- The 5-year range (2020-2024) provides enough volume for meaningful pattern analysis (hundreds of thousands of complaints)
- Focused timeframe keeps file size manageable while still being recent and relevant
- The static file URL enables direct programmatic download without API complexity

**Implementation:**
```python
requests.get(url) → save ZIP → extract with zipfile → tab-delimited TXT file
```

**Alternative Approaches Considered:**
- **2025-Only File**: Exists at https://static.nhtsa.gov/odi/ffdd/cmpl/COMPLAINTS_RECEIVED_2025.zip, but contains too little data for trend analysis at this point in the year.
- **Full Historical Archive**: Could download all complaints back to the 1990s, but the file size would be excessive for this assessment and processing would be slower.
- **NHTSA API**: Available at https://www.nhtsa.gov/nhtsa-datasets-and-apis, but the complaints endpoint requires constructing queries by make/model/year, making it impractical to retrieve the full dataset. The bulk download is the recommended approach even in NHTSA's own documentation.

---

### 3. DOE Alternative Fuel Stations Data

**Source:** NREL Alternative Fuel Stations API (https://developer.nrel.gov/api/alt-fuel-stations/v1)
**Output:** `data/raw/alt_fuel_stations.csv` (~96,829 stations)

This dataset tracks the locations and details of alternative fuel infrastructure across the U.S., including EV charging stations, hydrogen refueling points, propane, natural gas, and biodiesel stations. Fields include latitude/longitude, fuel type, access type (public/private), station status, opening date, network affiliation, and pricing information.

**Why the API Approach:**

The assessment-provided link (https://afdc.energy.gov/data_download) serves the same underlying data, but it requires filling out a web form with contact information and a use-case description before each download. This creates two problems:

1. **Breaks Automation**: Every script run would require manual intervention, contradicting the core requirement of building a repeatable, schedulable pipeline.
2. **Not Scalable**: In a production environment, this workflow couldn't run unattended or be integrated into scheduled jobs.

The NREL API provides programmatic access to the identical dataset maintained by the DOE Alternative Fuels Data Center. It's the official interface for automated data retrieval, designed specifically for use cases like this.

**Implementation:**
```python
Load API key from environment variable (.env file)
→ Request JSON from API with limit=all
→ Parse JSON response
→ Convert to pandas DataFrame
→ Export as CSV for consistency with other sources
```

Error handling covers:
- Missing API key: Prints setup instructions
- Failed API request: Shows status code and suggests manual fallback
- Empty response: Reports no data found

**API Key Management:**
- The key is stored in a `.env` file in the project root
- `.env` is listed in `.gitignore`, so the key never gets committed to version control
- `.env.example` is committed to show what variables are needed
- Standard security practice: demonstrates understanding of credential management in real-world pipelines

**Alternative Approaches Considered:**

**Option A: Manual Download from Web Form**
- **Pros**: Uses the exact assessment-provided link; no external dependencies
- **Cons**: Requires human interaction for every run; can't be scheduled; fails the automation requirement
- **Verdict**: Not viable for a production pipeline

**Option B: NREL API (Chosen Approach)**
- **Pros**: Official programmatic interface; designed for automation; returns structured JSON; supports full dataset retrieval; free and publicly available
- **Cons**: Requires a one-time signup (2 minutes) and environment variable configuration
- **Verdict**: The correct engineering solution. The API is the DOE's intended method for automated access.

**Getting the API Key:**
1. Go to https://developer.nrel.gov/signup/
2. Enter name and email
3. Confirm via email link
4. Receive API key immediately (free, no approval needed)
5. Add to `.env` file: `NREL_API_KEY=your_key_here`

---

## How Automation Works

### Running the Script
```bash
python scripts/acquire_data.py
```

Expected output:
```
EPA data downloaded and unzipped to data/raw/vehicles.csv
NHTSA complaints data downloaded and unzipped to data/raw/
Alternative fuel stations data downloaded: 96829 stations saved to data/raw/alt_fuel_stations.csv
```

### Prerequisites
- Python 3.x with `requests`, `pandas`, and `python-dotenv` packages
- API key configured in `.env` file (for alternative fuel stations only)

### What Gets Automated
1. **HTTP Downloads**: All files are fetched programmatically via `requests.get()`
2. **File Extraction**: ZIP files are automatically unzipped
3. **Format Conversion**: API JSON is converted to CSV to match other sources
4. **Error Handling**: Failed requests report status codes; missing API keys print setup instructions
5. **Directory Creation**: `data/raw/` is created if it doesn't exist

### No Manual Steps Required
Once the API key is set up (one-time), the entire script runs without human intervention. This means it can be:
- Scheduled with cron (Linux/Mac) or Task Scheduler (Windows)
- Integrated into CI/CD pipelines
- Run on a server or cloud instance
- Triggered by workflow automation tools

This will be restudied in the future.

### Why Full Automation Matters
In a real data engineering context, pipelines need to refresh data on a schedule—daily, weekly, or when upstream sources update. Manual steps create bottlenecks, introduce errors, and don't scale. This script demonstrates that all three sources can be acquired programmatically, meeting the assessment's emphasis on repeatability and automation.

---

## Design Decisions

### Modular Structure
Each data source is handled in its own section with independent error handling. If EPA fails, NHTSA and DOE still run. This makes debugging easier and prevents one broken source from blocking the entire pipeline.

### Consistent Output Format
All datasets are saved as CSV files in `data/raw/`, even though the API returns JSON. This consistency simplifies the next pipeline stage (data processing and transformation), where all sources can be read with `pandas.read_csv()`, for example.

### Transparency and Logging
Print statements show exactly what's happening at each step. In a production system, these would be replaced with proper logging (e.g., Python's `logging` module), but for this assessment, simple prints provide clear feedback during development and testing.

### Security Best Practices
The API key is never hardcoded in the script or committed to Git. Using environment variables demonstrates real-world credential management. The `.env.example` file documents what's needed without exposing secrets.

---

## Trade-offs and Rationale Summary

| Data Source | Chosen Method | Why | Alternative Rejected |
|-------------|---------------|-----|----------------------|
| EPA Fuel Economy | Bulk ZIP download | Simplest, fastest, most reliable | API requires pagination |
| NHTSA Complaints | Bulk ZIP download | Complete dataset in one file | API awkward for full retrieval |
| DOE Alt Fuel Stations | NREL API | Only way to fully automate | Web form requires manual input |
 
It was decided to **choose the method that best supports automation while maintaining reliability and simplicity**.
For EPA and NHTSA, bulk files win. For DOE, the API is the only viable path to true automation.
