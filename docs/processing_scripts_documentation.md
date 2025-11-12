# Processing Scripts Documentation

This document walks through what each processing script does and why. The goal is to help you understand the cleaning logic by reading this alongside the code.

---

## EPA Vehicles Processing (`process_epa.py`)

**Input:** `data/raw/vehicles.csv`
**Output:** `data/processed/epa_vehicles_clean.csv`

### What's being done here

The EPA file contains every vehicle sold in the US since 1984. That's a lot of data, but most of it isn't useful for analyzing modern fuel efficiency trends. It was filtered down to recent vehicles (2010+) and removing anything that's clearly wrong or redundant.

### Step 1: Load the raw data

Simple CSV read, the `low_memory=False` flag tells pandas to look at the whole file before deciding what data type each column should be. This prevents issues where pandas guesses wrong based on just the first few rows.

### Step 2: Filter to 2010 and later

It was decided to keep only vehicles from 2010 forward. Because pre-2010 vehicles represent outdated technology (assumption), and the NHTSA complaints dataset only covers 2020-2024. 

This single filter removes about 60% of the records.

### Step 3: Remove records with missing critical fields

A vehicle record is useless if it's not clear what it is (make/model/year) or how efficient it is (MPG) - assumption. Any row missing these core identifiers is dropped.

For MPG, there's flexibility: the record just needs *at least one* MPG value (combined, city, or highway). It was used `notna()` to check if a value exists and `|` (OR) to say "keep the row if *any* of these MPG columns has data."

This step removes very few or any records because the EPA dataset is well-maintained.

### Step 4: Remove obvious outliers

Three types of bad data get removed in this step:

**MPG = 0:** If a vehicle is in the database, it uses fuel. Zero MPG means data entry error.

**MPG > 200 (unless electric):** It was assumed that no gas vehicle gets 200 MPG or more. Hybrids normally top out around 50-60 MPG. But electric vehicles are measured in MPGe (miles per gallon *equivalent*), and they can hit 100-150 MPGe. So it was only removed >200 MPG, if the fuel type doesn't contain "Electric."

**Future years:** If a record says it's a 2027 model and the current year is 2025, that's a data quality issue. For that, it was used `datetime.now().year` to get the current year dynamically, so this check stays valid as time passes, with automation in mind.

### Step 5: Remove exact duplicates

Two records are considered duplicates if they match on *all* of these fields: year, make, model, engine displacement, cylinders, transmission, drive type, fuel type, and all three MPG values.

They're all considered, because a 2020 Honda Accord LX (2.0L, CVT, FWD, 30 MPG) is different from a 2020 Honda Accord EX (different trim, different specs). Only rows that are *completely* identical are dropped, which usually means system errors where the same record was inserted twice.

`keep='first'` was used to keep the first occurrence of each duplicate and drop the rest.

### Step 6: Select relevant columns

Most if the columns are niche fields like "fuel cost per year in 2008 dollars" or "EPA vehicle size class code.". It was narrowed down to 16 essential columns:

- Vehicle identifiers: year, make, model, class
- Performance specs: engine displacement, cylinders, transmission, drive type
- Fuel data: primary_fuel, secondary_fuel (renamed from fuelType1/fuelType2 for semantic clarity), city/highway/combined MPG
- Emissions: CO2 grams per mile
- Reference: original EPA ID

Everything else gets dropped to keep the output file clean and focused.

### Step 7: Handle dual-fuel vehicles (explosion)

**New step added to correctly handle plug-in hybrids and flex-fuel vehicles.**

Vehicles with `secondary_fuel` (like plug-in hybrids) need to be counted in infrastructure analysis for BOTH fuel types they support.

**Solution**: "Explode" dual-fuel vehicles into multiple rows. The script:
1. Renames EPA's `fuelType1` → `primary_fuel` and `fuelType2` → `secondary_fuel` (semantic naming)
2. For each vehicle with a non-null `secondary_fuel`, creates TWO rows:
  - Row 1: `fuel_used` = `primary_fuel`, `fuel_rank` = 1
  - Row 2: `fuel_used` = `secondary_fuel`, `fuel_rank` = 2
3. Single-fuel vehicles get one row with `fuel_used` = `primary_fuel`, `fuel_rank` = 1

**Example**:
- **Before**: 1 row for 2011 Chevy Volt (primary_fuel='Premium Gasoline', secondary_fuel='Electricity')
- **After**: 2 rows for 2011 Chevy Volt
  - Row 1: fuel_used='Premium Gasoline', fuel_rank=1
  - Row 2: fuel_used='Electricity', fuel_rank=2

**Impact**: ~1,500 dual-fuel vehicles create ~3,094 extra rows. Output goes from ~20,000 → ~22,000 vehicle-fuel combinations.

This is important because, when analyzing fuel infrastructure needs, plug-in hybrids do use EV charging stations AND gas stations. Counting them in both categories accurately reflects infrastructure demand.

### Step 8: Save and summarize

The cleaned data was saved to CSV. The summary now shows:
- Initial raw records
- Records after cleaning (before explosion)
- Final records after dual-fuel explosion
- Note that rows now represent vehicle-fuel combinations, not unique vehicles

---

## NHTSA Complaints Processing (`process_nhtsa.py`)

**Input:** `data/raw/COMPLAINTS_RECEIVED_2020-2024.txt` 
**Output:** `data/processed/nhtsa_complaints_clean.csv` 

### What's been done here

The NHTSA file contains consumer complaints about vehicle safety issues filed between 2020 and 2024. Unlike the EPA file, this one has a weird structure. It's tab-separated with no header row. The first row is actual data, not column names.

This means that it's needed to manually map column positions to meaningful names.

### Step 1: Load the raw data with column mapping

Here's where `usecols` comes in. The file has 49 columns, but it's only needed 14 of them. Instead of reading all 49 and then selecting what's needed, pandas is being told "only read columns 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 14, and 17."

Then those 14 columns are named using the `names` parameter:
- Column 0 → ODINO (complaint ID)
- Column 1 → CMPLID
- Column 2 → MFGTXT (manufacturer)
- Column 3 → MAKETXT (vehicle make)
- Column 4 → MODELTXT (vehicle model)
- Column 5 → YEARTXT (vehicle year)
- Column 6 → CRASH (Y/N flag)
- Column 7 → DATEA (date complaint received)
- Column 8 → FIRE (Y/N flag)
- Column 9 → INJURED (number of injuries)
- Column 10 → DEATHS (number of deaths)
- Column 11 → COMPDESC (failed component description)
- Column 14 → VIN (vehicle ID number)
- Column 17 → MILEAGE

Columns 12-13, 15-16 were skipped, and 18-48 because they're either redundant or not useful for our analysis (assumption).

### Step 2: Remove records with missing critical fields

Same idea as EPA: a complaint is useless if it remains unknown which vehicle it’s about or when it was filed. Any row missing the complaint ID, date, vehicle year, make or model is dropped.

This removes very few records out of 418,787. The NHTSA data is pretty clean in this regard.

### Step 3: Data type conversions and outlier removal

This is where things get interesting. The date and year columns come in as numbers or strings, not proper date/numeric types. Convertion is needed.

**Date conversion:** DATEA comes in as `20191221` (YYYYMMDD format). It was converted to a proper datetime object using `pd.to_datetime()` with `format='%Y%m%d'`. The `errors='coerce'` means "if you can't convert it, just make it NaN instead of crashing."

**Year conversion:** YEARTXT is text like "2018". It was converted to numeric with `pd.to_numeric()`.

Then outliers are removed:
- Complaints with future dates (data entry errors)
- Mileage > 1,000,000 miles (no car lasts that long)
- Vehicle years in the future

This removes about 6,000 records.

### Step 4: Remove exact duplicates

Each complaint should have a unique ODINO (complaint ID). If the same ODINO appears twice, it's a system duplicate. Duplicated are dropped based on ODINO alone.

Interestingly, there are *zero* duplicates in this dataset. NHTSA's database has good unique constraints.

### Step 5: Convert date back to string

DATEA was converted to datetime for validation, but when its saved to CSV, datetime objects get messy, so it was converted again to a clean string format (`YYYY-MM-DD`) using `strftime()`.

This makes the CSV file easier to read and more portable.

### Step 6: Convert numeric fields to integers

To improve readability in the CSV file, numeric fields are converted to integers to avoid the `.0` formatting (e.g., `2018` instead of `2018.0`):

**YEARTXT conversion:** Since all critical year values are present (no nulls after filtering), YEARTXT is converted to standard `int64`. This ensures the CSV displays years as `2018` rather than `2018.0`.

**MILEAGE handling:** MILEAGE has a big percentage of nulls. It was converted to `Int64` (nullable integer) during processing, but when saved to CSV, pandas must use `float64` to represent NaN values. This is a CSV format limitation - there's no way to store integers with null values in plain CSV without using float. The values appear as `15000.0` or `NaN` in the file, which is acceptable since MILEAGE is an optional field.

### Step 7: Save and summarize

Same as EPA: save to CSV and print a summary. A big percentage of the record were kept, meaning that most of the data is clean, just removing a few thousand outliers.

---

## DOE Fuel Stations Processing (`process_doe.py`)

**Input:** `data/raw/alt_fuel_stations.csv` 
**Output:** `data/processed/doe_fuel_stations_clean.csv`

### What's being done here

The DOE file contains alternative fuel station locations across the United States. This includes electric vehicle charging stations, CNG, LNG, biodiesel, E85, and hydrogen stations. The data is relatively clean but needs geographic validation and filtering to focus on truly alternative fuels.

### Step 1: Load the raw data

Simple CSV read with `low_memory=False` to ensure proper data type inference across all 76 columns. The DOE data comes from the NREL API and is well-structured with headers.

### Step 2: Remove records with missing critical fields

A fuel station record is useless if its location is unknown or the fuel type is missing (assumption). Any row missing latitude, longitude, fuel_type_code, or status_code is dropped.

The DOE dataset is very well-maintained, so this step removes zero records. All critical fields are present.

### Step 3: Remove obvious outliers

Two types of geographic errors are removed:

**Coordinates outside U.S. bounds:** For this project, it was assumed that valid U.S. fuel stations must be within latitude 18-72 (Hawaii to Alaska) and longitude -180 to -65 (West to East Coast). These ranges were chosen to cover all U.S. territories including Alaska and Hawaii. This catches data entry errors where coordinates might be swapped or incorrect.

**Zero coordinates (0,0):** If both latitude and longitude are exactly zero, it's a clear data entry error (the real 0,0 coordinate is in the Gulf of Guinea off the coast of Africa).

This step removes only 2 records, confirming the data quality is excellent.

### Step 4: Remove exact duplicates

Each station should have a unique ID. If the same ID appears twice, it's a system duplicate. Duplicates are dropped based on the ID field.

Interestingly, there are *zero* duplicates in this dataset. The DOE database has strong unique constraints.

### Step 5: Filter to relevant alternative fuel types

The raw data includes some non-alternative fuel stations (gasoline, diesel). Only truly alternative fuel types are kept:
- **ELEC** - Electric vehicle charging
- **LNG** - Liquefied natural gas
- **CNG** - Compressed natural gas
- **BD** - Biodiesel
- **E85** - 85% ethanol blend
- **HY** - Hydrogen


### Step 6: Select relevant columns

Most of the columns are specialized fields for specific analyses. It was narrowed down to 15 essential columns:

- Fuel information: fuel_type_code
- Station identification: station_name, id
- Location details: street_address, city, state, zip, latitude, longitude
- Operational info: status_code, access_code, open_date
- EV-specific: ev_network, ev_connector_types, ev_pricing (for electric stations)

Everything else is dropped to keep the output focused.

**Note on EV-specific fields:** The three EV columns (ev_network, ev_connector_types, ev_pricing) are only populated for ELEC (electric charging) stations. For other fuel types like CNG, LNG, BD, E85, and HY, these fields naturally contain empty values (NaN). This is expected behavior, not a data quality issue. Since the most part of the stations in the cleaned dataset are ELEC, most records have these fields populated. The remaining (CNG, LNG, BD, E85, HY) will show empty values for EV-specific fields because these columns don't apply to non-electric fuel infrastructure.

### Step 7: Save and summarize

The cleaned data was saved to CSV and a summary was printed. Most of the records were kept, showing that the DOE data is already very clean with minimal data quality issues.

---

## Key Differences Between the Three Scripts

**EPA:** Heavy filtering. Strategic choices were made about what time period and data quality is needed. Temporal filtering from 2010+ removes the majority of records.

**NHTSA:** Light cleaning. The data is already pretty clean, it was only needed to fix types and to remove obvious errors.

**DOE:** Minimal cleaning. Excellent data quality from the source. Main task is filtering to alternative fuels and validating geographic coordinates.

**EPA:** File has headers, normal CSV structure.

**NHTSA:** No headers, tab-separated, required manual column mapping with `usecols`.

**DOE:** File has headers, normal CSV structure from API response.

**EPA:** Focused on deduplication across multiple fields (year + make + model + specs).

**NHTSA:** Focused on single-field deduplication (ODINO).

**DOE:** Focused on single-field deduplication (station ID).

All three scripts follow the same general flow: load → clean critical fields → remove outliers → deduplicate → select columns → save. The specifics vary based on what the data looks like and what is trying to be accomplished.
