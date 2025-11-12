# Data Processing Strategy & Initial Decisions

## Overview

This document outlines the strategy and key decisions made before beginning the data processing and transformation phase. After successfully acquiring three automotive datasets (EPA, NHTSA, DOE), the next step is to clean, transform, and integrate this raw data into analysis-ready formats.

The goal is not to achieve perfect cleanliness, but to make thoughtful, documented decisions that balance data quality with practical constraints. This document serves as a decision log and reference for the processing work ahead.

---

## Dataset Summary (From Acquisition)

### 1. EPA Vehicle Fuel Economy Data
**Source:** U.S. Environmental Protection Agency
**Records:** 49,582 vehicles (1984–present)
**Columns:** 84

**Key Fields:**
- `year` - Model year
- `make`, `model` - Vehicle identification
- `city08`, `highway08`, `comb08` - MPG ratings (city, highway, combined)
- `primary_fuel`, `secondary_fuel` - Fuel types (semantic naming)
- `fuel_used` - The specific fuel type this row represents (after explosion)
- `fuel_rank` - Fuel priority rank: 1=primary, 2=secondary
- `co2TailpipeGpm` - CO2 emissions (grams per mile)
- `VClass` - Vehicle class (sedan, SUV, pickup, etc.)
- `cylinders`, `displ` - Engine specs (cylinder count, displacement)
- `trany` - Transmission type

**Purpose:** Analyze fuel efficiency trends, emissions, and vehicle characteristics over time.

---

### 2. NHTSA Vehicle Complaints Data
**Source:** National Highway Traffic Safety Administration
**Records:** 418,786 complaints (2020–2024)
**Columns:** 49 (note: file has header issues that need fixing during processing)

**Key Fields:**
- `ODINO` - Unique complaint ID
- `DATEA` - Date complaint received
- `MAKETXT`, `MODELTXT`, `YEARTXT` - Vehicle identification
- `CMPLID` - Complaint summary (free text)
- `COMPDESC` - Component that failed
- `CRASH`, `FIRE`, `INJURED` - Incident severity flags
- `MILEAGE` - Odometer reading at time of complaint

**Purpose:** Identify safety issues, recurring defects, and complaint patterns by vehicle make/model.

---

### 3. DOE Alternative Fuel Stations Data
**Source:** U.S. Department of Energy (via NREL API)
**Records:** 96,829 stations
**Columns:** 76

**Key Fields:**
- `latitude`, `longitude` - Station coordinates
- `fuel_type_code` - Type of fuel (ELEC, LNG, CNG, BD, E85, HY, etc.)
- `station_name` - Station identifier
- `status_code` - Operational status (E = available, P = planned, T = temporarily unavailable)
- `access_code` - Public or private access
- `state` - U.S. state
- `open_date` - When the station opened
- `ev_network` - Charging network (ChargePoint, Tesla, etc.)

**Purpose:** Map alternative fuel infrastructure growth and availability across the U.S.

---

## Key Processing Decisions

### 1. Temporal Filtering

**Decision: Focus on 2010 Forward**

**Rationale:**
- Pre-2010 vehicles represent outdated technology and have significant missing data for modern metrics (hybrid/EV range, updated emissions standards)
- The NHTSA dataset only covers 2020–2024, so matching with very old EPA records provides limited value
- Alternative fuel infrastructure is a modern phenomenon. Most, or a lot more, stations opened after 2010
- 15 years of data (2010–2025) is sufficient for identifying trends without sacrificing data quality

**Trade-off:**
Historical perspective is lost on how fuel economy evolved from the 1980s onward, but cleaner data is achieved and more relevant comparisons.

**What Gets Filtered:**
- EPA: Keep only `year >= 2010`
- NHTSA: Already 2020+ (no additional filtering needed)
- DOE: Keep all (most stations are recent)

---

### 2. Missing Value Strategy

**Decision: Drop Critical, Tolerate Optional**
At first, the initial thoughts is to drop critical (which is missing values) but tolerate optional fields that might have some missing values.

**Critical Fields (Must Have):**

| Dataset | Must-Have Fields | Action if Missing |
|---------|------------------|-------------------|
| EPA | `year`, `make`, `model`, at least one MPG column (`comb08` or `city08`/`highway08`) | **Drop row** |
| NHTSA | `ODINO`, `YEARTXT`, `MAKETXT`, `MODELTXT`, `DATEA` | **Drop row** |
| DOE | `latitude`, `longitude`, `fuel_type_code`, `status_code` | **Drop row** |

**Optional Fields (Can Be Null):**

| Dataset | Optional Fields | Handling |
|---------|-----------------|----------|
| EPA | `co2TailpipeGpm`, electric range, some engine specs | Keep row, leave as null or flag |
| NHTSA | `VIN`, `MILEAGE`, incident flags (`CRASH`, `FIRE`) | Keep row, analysis may exclude these fields if needed |
| DOE | `ev_network`, pricing, access hours | Keep row, reflects real-world incomplete data |

**Why:**
A vehicle can't be analyzed if it's not clear what it is (make/model/year) or how efficient it is (MPG). But it's tolerated to miss secondary attributes like CO2 or mileage because they don't invalidate the core record.

**Expected Impact:**
Minimal row loss for EPA and DOE (these fields are well-populated). Some NHTSA row loss if complaint IDs or vehicle identifiers are missing, but that's acceptable because incomplete complaints aren't useful.

---

### 3. Outlier Handling - Remove or Investigate

**Decision: Flag First, Remove Only if Clearly Erroneous**

**Approach:**
1. **Identify outliers statistically** using IQR (Interquartile Range) to flag values that fall far outside the normal range.
2. **Inspect flagged records** - are they legitimate edge cases or data errors?
3. **Remove only obvious errors (initial values)**:
   - EPA: MPG (Miles Per Gallon) values > 200 (unless it's an EV with MPGe), MPG = 0, year in future
   - NHTSA: Complaint dates in the future, mileage > 1,000,000 miles
   - DOE: Coordinates outside U.S. bounds (lat/lon = 0 or in the ocean)
4. **Keep legitimate extremes (examples)**:
   - EPA: Tesla Model S with 100+ MPGe (real), heavy trucks with <15 MPG (real)
   - NHTSA: Vehicles with 500+ complaints (likely recalls, important to keep)
   - DOE: Stations in Alaska/Hawaii (unusual coordinates but valid)

**Assumptions:**
The 200 MPG threshold assumes that no production gas vehicle can exceed 150 MPG in real-world conditions (most hybrids max out at 50-60 MPG). Electric vehicles are exempt because they use MPGe (MPG-equivalent), which can legitimately reach 100-150+ for efficient EVs. The 1,000,000 mile threshold for NHTSA complaints assumes that values beyond this are data entry errors, as the average car lasts 150,000-200,000 miles and even commercial vehicles rarely exceed 500,000 miles.

**Why:**
Blindly removing outliers loses valuable information. High complaint counts indicate real problems. Extreme MPG values are often legitimate (EVs, hybrids). Manual inspection is worth the effort.

**What Gets Removed:**
- EPA: Vehicles with MPG > 200 unless `fuel_used` contains "Electric"
- DOE: Stations with `latitude < 24` or `> 50`, `longitude < -125` or `> -65` (rough US bounds)
- NHTSA: Complaints with `DATEA` after today's date

---

### 4. Duplication Strategy

**Decision: Context-Specific Deduplication**

**EPA Vehicles:**
- **Fuzzy matching needed** - same year/make/model but different trims are NOT duplicates
- **Rule:** Drop exact duplicates across all key fields (year, make, model, engine size, transmission, MPG)
- **Example:** "2020 Honda Accord LX" vs "2020 Honda Accord EX" = **keep both** (different trims)
- **Example:** Two identical rows of "2020 Honda Accord LX 2.0L CVT 30 MPG" = **drop one**

**NHTSA Complaints:**
- **Strict deduplication** using `ODINO` (complaint ID)
- **Rule:** If the same `ODINO` appears multiple times, keep the first occurrence
- **Rationale:** This is a system duplicate. Each complaint should have an unique ID

**DOE Fuel Stations:**
- **Keep separate rows for multi-fuel stations**
- **Rule:** If a station at the same lat/lon offers both electric and hydrogen, keep both rows
- **Why:** Fuel-specific analysis is more useful than aggregating. A station that offers EV + CNG is serving two distinct use cases.

---

### 5. Integration Scope

**Decision: Produce 3 Clean Datasets + 1 Integrated Summary**

**Primary Deliverables:**
1. `data/processed/epa_vehicles_clean.csv` - Cleaned EPA fuel economy data
2. `data/processed/nhtsa_complaints_clean.csv` - Cleaned NHTSA complaints
3. `data/processed/doe_fuel_stations_clean.csv` - Cleaned DOE stations

**Bonus Integration:**
4. `data/processed/vehicle_complaints_summary.csv` - EPA + NHTSA joined on (year, make, model)

**Why This Approach?**
- The assessment requires cleaning and integration, but full integration of all three datasets is artificial
- DOE fuel stations don't naturally join with vehicle-level data (it's infrastructure, not vehicle-specific)
- A **strategic join** of EPA + NHTSA shows integration capability without forcing unnatural relationships

**Join Strategy (EPA + NHTSA):**
- **Match on:** `year`, `make`, `model` (case-insensitive, spaces removed for consistency)
- **Goal:** Create a summary table showing:
  - Vehicle make/model/year
  - Average MPG (from EPA)
  - Total complaint count (from NHTSA)
  - Most common complaint type
- **Challenge:** Make/model names aren't always standardized ("Chevrolet" vs "CHEVY", "F-150" vs "F150")
- **Solution:** Normalize names before joining (uppercase, remove hyphens/spaces, standardize common abbreviations)

**Expected Output (example):**
A table like this:
| Year | Make | Model | Avg_MPG | Complaint_Count | Top_Issue |
|------|------|-------|---------|-----------------|-----------|
| 2020 | Toyota | Camry | 32 | 47 | Engine |
| 2021 | Ford | F150 | 22 | 203 | Transmission |

Richer analysis is achieved, with this method.
---

### 6. Dual-Fuel Vehicle Handling

**Decision: Explode into Multiple Rows**

**Problem:**
EPA raw data includes both `fuelType1` (primary) and `fuelType2` (secondary) columns. Approximately 1,514 vehicles support multiple fuel types:
- **Plug-in hybrids**: Primary=Gasoline, Secondary=Electricity (e.g., Chevy Volt, Prius Plug-in, Ford C-MAX Energi)
- **Flex-fuel vehicles**: Primary=Gasoline, Secondary=E85

When aggregating by fuel type for infrastructure analysis, we need to count plug-in hybrids in BOTH the Gasoline and Electricity categories, since they use both types of infrastructure.

**Solution:**
"Explode" dual-fuel vehicles into multiple rows - one row per fuel type. The processing script:
1. Renames `fuelType1` → `primary_fuel`, `fuelType2` → `secondary_fuel` (semantic naming)
2. Creates `fuel_used` column (which specific fuel this row represents)
3. Creates `fuel_rank` column (1=primary, 2=secondary, future-proof for tri-fuel)

Example - 2011 Chevy Volt creates TWO rows:
- Row 1: `fuel_used='Premium Gasoline'`, `fuel_rank=1`
- Row 2: `fuel_used='Electricity'`, `fuel_rank=2`

**Impact:**
- Processed EPA data goes from ~19,810 rows → ~21,357 rows (+1,547 extra rows)
- Rows now represent "vehicle-fuel combinations" rather than unique vehicles
- Infrastructure analysis correctly counts plug-in hybrids in both fuel type categories
- This accurately reflects infrastructure demand

**Trade-off:**
Vehicle counts become ambiguous (need to specify "unique vehicles" vs "vehicle-fuel combinations"), but infrastructure planning becomes more accurate.

---

### 7. Text Field Cleaning

**Decision: Standardize for Joining**

**Process:**
- **Uppercase** make/model names for case-insensitive matching
- **Strip leading/trailing whitespace**
- Special characters and abbreviations are kept as-is (simple normalization approach)

**Why:**
The goal is to make datasets **joinable**, so simple standardization is enough to enable merging.
