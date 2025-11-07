# Processing Scripts Documentation

This document walks through what each processing script does and why. The goal is to help you understand the cleaning logic by reading this alongside the code.

---

## EPA Vehicles Processing (`process_epa.py`)

**Input:** `data/raw/vehicles.csv` (49,582 records, 84 columns)
**Output:** `data/processed/epa_vehicles_clean.csv` (19,952 records, 15 columns)
**Retention rate:** 40.2%

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

The raw file has 84 columns. Most are niche fields like "fuel cost per year in 2008 dollars" or "EPA vehicle size class code.". It was narrowed down to 15 essential columns:

- Vehicle identifiers: year, make, model, class
- Performance specs: engine displacement, cylinders, transmission, drive type
- Fuel data: fuel type (primary and secondary), city/highway/combined MPG
- Emissions: CO2 grams per mile
- Reference: original EPA ID

Everything else gets dropped to keep the output file clean and focused.

### Step 7: Save and summarize

The cleaned data was saved to CSV and then a summary showing how many records were at the start, how many were kept, and how the column count changed is printed. This gives us a quick sanity check that the process worked as expected.

---

## NHTSA Complaints Processing (`process_nhtsa.py`)

**Input:** `data/raw/COMPLAINTS_RECEIVED_2020-2024.txt` (418,787 records, 49 columns)
**Output:** `data/processed/nhtsa_complaints_clean.csv` (412,704 records, 14 columns)
**Retention rate:** 98.5%

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

<!-- CONFIRME THIS up -->

### Step 6: Save and summarize

Same as EPA: save to CSV and print a summary. 98.5% of the record were kept, meaning that most of the data is clean, just removing a few thousand outliers.

---

## Key Differences Between the Two Scripts

**EPA:** Heavy filtering (60% removed). Strategic choices were made about what time period and data quality is needed.

**NHTSA:** Light cleaning (1.5% removed). The data is already pretty clean, it was only needed to fix types and to remove obvious errors.

**EPA:** File has headers, normal CSV structure.

**NHTSA:** No headers, tab-separated, required manual column mapping with `usecols`.

**EPA:** Focused on deduplication across multiple fields (year + make + model + specs).

**NHTSA:** Focused on single-field deduplication (ODINO).

Both scripts follow the same general flow: load → clean critical fields → remove outliers → deduplicate → select columns → save. The specifics vary based on what the data looks like and what is trying to be accomplished.
