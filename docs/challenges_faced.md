# Challenges Faced

This document covers the main issues/challenges encountered during the pipeline development and how they were solved.

## Data Acquisition Strategy

There was an early decision to make: download data via APIs/bulk files or committing pre-downloaded CSV files to the repository.

Committing pre-downloaded CSV files would make the pipeline simpler and faster to run. Anyone could clone the repo and immediately run the processing scripts without needing API keys or internet access. The data files would be version-controlled alongside the code.

However, the choice was to download data programmatically in order to promote automation. EPA and NHTSA provide bulk ZIP files which are downloaded directly. DOE requires an NREL API key for alternative fuel stations data. This approach keeps data fresh and demonstrates real acquisition patterns, though it requires internet access and API credentials. It also shows how a production pipeline would work, where data is fetched from source systems rather than committed to version control.

The --skip-data flag was added to run_pipeline.py to allow reprocessing existing data without re-downloading, which helps during development and testing.

## Matching Vehicles Across Sources

Each data source uses different naming conventions. EPA might have "Ford F150", NHTSA could have "Ford F-150" or "FORD F150" in all caps. There's no standardized vehicle identifier across the three sources.

The join strategy normalizes by uppercasing make/model names and matching on year + make + model. A left join is used to keep all EPA vehicles. Those without matching complaints simply get 0 for complaint fields.

A big percentage of EPA vehicles have zero complaints in the integrated dataset. This is expected behavior, not a data quality issue. Most vehicles don't have safety complaints filed, only those with notable problems get owner complaints submitted to NHTSA. The little percentage of vehicles that do have complaints represent problematic vehicles, which is exactly the signal needed for safety analysis.

Some complaint matches might still be missed due to name variations (like "F150" vs "F-150") or trim levels being treated as separate models, but the match rate is reasonable given that most vehicles legitimately have no complaints.

The fuel infrastructure dataset aggregates by fuel type rather than individual vehicles, so the matching is simpler, which was to map EPA fuel codes to DOE fuel types.

## NHTSA Complaint Aggregation

Raw NHTSA data has one row per complaint. A single vehicle model can have hundreds of separate complaint records. This needed to be rolled up to vehicle level to join with EPA data.

Aggregations were created using pandas groupby for metrics like total_complaints, crash_incidents, fire_incidents. The challenge was parsing the free-text "components" field to categorize incidents. String matching was used but it's not perfect because the text format is inconsistent.

Null handling was also tricky because complaints without mileage are excluded from averages, but vehicles with zero crashes get crash_incidents=0 rather than null.

## DOE Data Limitations

The DOE alternative fuel stations API returns current snapshot data only. There's no historical data about how many stations existed in previous years.

The workaround was to keep the current station count and replicate it across all years in the integration step. This is obviously wrong for historical analysis but there's no alternative without time-series data. This limitation was documented in the processing strategy.

The API requires authentication (NREL key) which was handled using python-dotenv to load from a .env file.

## Dual-Fuel Vehicle Handling -> Biggest Challenge

### The Problem

The EPA raw data includes both `fuelType1` (primary fuel) and `fuelType2` (secondary fuel) columns. Approximately 1,500 vehicles in the 2010+ dataset support multiple fuel types:

- **plug-in hybrids**: Primary=Gasoline, Secondary=Electricity (Chevy Volt, Prius Plug-in, Ford C-MAX Energi, etc.)
- **flex-fuel vehicles**: Primary=Gasoline, Secondary=E85 (Ford F-150 FFV, Chevy Silverado FFV, Toyota Tundra FFV, etc.)

The challenge was deciding how to handle these vehicles in the fuel infrastructure analysis. A plug-in hybrid like the Chevy Volt needs BOTH gasoline stations AND EV charging infrastructure. If we only kept the primary fuel (`fuelType1`), we'd categorize all plug-in hybrids as "Gasoline" vehicles, causing a significant undercount of vehicles that actually use EV charging infrastructure.

### Initial Approach Considered: Boolean Flag

The first approach considered was to keep vehicles as single rows but add a boolean flag like `supports_alternative_fuel` to identify vehicles that could use multiple fuel types. This would preserve the one-vehicle-per-row structure and avoid "inflating" row counts.

This approach was rejected, because:
- Infrastructure demand analysis requires counting vehicles by fuel type. With a flag approach, we'd still need special logic to decide: "Do we count this plug-in hybrid in the Gasoline category? The Electricity category? Both?"
- Aggregations become ambiguous: `COUNT(*) WHERE fuel_type='Electricity'` would miss plug-in hybrids unless we added complex CASE statements throughout all queries
- The flag doesn't solve the fundamental issue: one vehicle might use two different infrastructure types
- Analysts would need to remember to check the flag in every query, making the data error-prone

### Solution Implemented: Row Explosion with Semantic Schema

The processing script handles dual-fuel vehicles by "exploding" them into multiple rows. One row per fuel type supported. Additionally, the schema was refactored for clarity:

**Schema improvements:**
- Renamed `fuelType1` → `primary_fuel` and `fuelType2` → `secondary_fuel` (semantic not positional naming)
- Created `fuel_used` column (which specific fuel this row represents)
- Created `fuel_rank` column with integer values 1=primary, 2=secondary (easier for querying)
- Dropped redundant `fuelType` (EPA's combined field)

**Example: 2011 Chevrolet Volt creates TWO rows:**
```
Row 1: primary_fuel='Premium Gasoline', secondary_fuel='Electricity',
       fuel_used='Premium Gasoline', fuel_rank=1

Row 2: primary_fuel='Premium Gasoline', secondary_fuel='Electricity',
       fuel_used='Electricity', fuel_rank=2
```

**Benefits of this approach:**
- Accurate infrastructure counts: Plug-in hybrids are correctly counted in both gasoline and EV charging demand
- Simple aggregations: `COUNT(*) WHERE fuel_used='Electricity'` naturally includes both pure EVs (fuel_rank=1) and plug-in hybrids (fuel_rank=2)
- Preserved context: Both rows retain `primary_fuel` and `secondary_fuel`, so analysts can see the full picture
- SQL-friendly: Easy to filter (`WHERE fuel_rank=1` for primary fuel only, or include all rows for total infrastructure demand)
- Self-documenting: Column names clearly indicate what each field represents

**Trade-offs:**
- Row count increases from ~20,000 → ~22,000 (~1500/2000 rows for secondary fuel modes)
- "Vehicle count" becomes ambiguous because it must be specified "unique vehicles" vs "vehicle-fuel combinations"
- Slightly more complex to explain to stakeholders unfamiliar with the explosion pattern

However, the trade-off is worthwhile because infrastructure planning accuracy is more important than keeping row counts simple. When a transportation agency asks "how many vehicles need EV charging stations?", the answer must include plug-in hybrids, not just pure electric vehicles.

## CSV vs Parquet Format Decision

There was consideration of using Parquet for the final datasets because it's much smaller (~90% reduction) and faster to read. But this would require reviewers to have pyarrow installed and specialized tools to inspect the data.

The decision was to use CSV for simplicity and reviewability, make it easy for anyone to open the files in Excel or a text editor. A parquet_comparison.py script was created to demonstrate understanding of the tradeoff. Documentation notes that Delta Lake uses Parquet internally, so production would get the efficiency benefit anyway.

## Databricks Connection Simulation

The assessment asks for a loading strategy but doesn't provide actual Databricks access. The decision was to generate the SQL statements (CREATE TABLE, COPY INTO) and print them rather than executing them.

Comments and documentation make it clear this is simulated.

## Year Range and Data Sparsity

The raw EPA data goes back to 1984, but there was a decision to filter to 2010 forward during processing.

Filtering to 2010+ keeps the dataset focused on modern vehicles where all three data sources have reasonable coverage. This avoids having many older vehicles with no complaint or infrastructure data. The tradeoff was documented in the processing strategy.

## Null Handling in Joins

When joining EPA and NHTSA with a left join, vehicles with no matching complaints end up with null values for all complaint columns (total_complaints, crash_incidents, fire_incidents, etc.). This creates ambiguity, does null mean "no data available" or "zero complaints filed"?

The integration logic fills these nulls with 0, which assumes "no match = no complaints filed." This is implemented in integrate_data.py using `fillna(0)` on all numeric complaint fields.

This is probably the correct interpretation for most cases. If a vehicle has no records in NHTSA's complaint database, it most likely has zero complaints rather than missing data. The result is that most of vehicles have zero complaints, which is expected since most vehicles don't have safety issues reported.

Note that some EPA fields like cylinders and displ do have legitimate nulls (about 1,100 vehicles), likely electric vehicles without traditional engines. These nulls are preserved because they represent genuinely missing or inapplicable data.

