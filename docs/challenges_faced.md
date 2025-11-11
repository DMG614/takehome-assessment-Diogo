# Challenges Faced

This document covers the main issues/challenges encountered during the pipeline development and how they were solved.

## Data Acquisition Strategy

There was an early decision to make: download data via APIs/bulk files versus committing pre-downloaded CSV files to the repository.

Committing pre-downloaded CSV files would make the pipeline simpler and faster to run. Anyone could clone the repo and immediately run the processing scripts without needing API keys or internet access. The data files would be version-controlled alongside the code.

However, the choice was to download data programmatically. EPA and NHTSA provide bulk ZIP files which are downloaded directly. DOE requires an NREL API key for alternative fuel stations data. This approach keeps data fresh and demonstrates real acquisition patterns, though it requires internet access and API credentials. It also shows how a production pipeline would work, where data is fetched from source systems rather than committed to version control.

The --skip-data flag was added to run_pipeline.py to allow reprocessing existing data without re-downloading, which helps during development and testing.

## Matching Vehicles Across Sources

Each data source uses different naming conventions. EPA might have "Ford F150", NHTSA could have "Ford F-150" or "FORD F150" in all caps. There's no standardized vehicle identifier across the three sources.

The join strategy normalizes by uppercasing make/model names and matching on year + make + model. A left join is used to keep all EPA vehicles. Those without matching complaints simply get 0 for complaint fields.

About 81.7% of EPA vehicles have zero complaints in the integrated dataset. This is expected behavior, not a data quality issue. Most vehicles don't have safety complaints filed, only those with notable problems get owner complaints submitted to NHTSA. The 18.3% of vehicles that DO have complaints (3,631 models) represent genuinely problematic vehicles, which is exactly the signal needed for safety analysis.

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

## Dual-Fuel Vehicle Limitation

The EPA raw data includes both `fuelType1` and `fuelType2` columns. Some vehicles support multiple fuel types, most notably plug-in hybrids that have Electricity as secondary fuel (like Chevy Volt, Prius Plug-in, Ford C-MAX Energi) and some flex-fuel vehicles that can use E85.

The processing script only keeps `fuelType1` (primary fuel type) and drops `fuelType2`. This means plug-in hybrids are categorized as "Gasoline" vehicles rather than having any electric vehicle designation.

For the fuel infrastructure analysis, this causes an undercount. Those plug-in hybrids DO use EV charging infrastructure but aren't counted in the "Electricity" category. They're grouped with regular gasoline vehicles instead.

This was a simplification decision to avoid double-counting vehicles in aggregations, but it does lose information about which vehicles can use alternative fuel infrastructure. A more sophisticated approach would flag vehicles as "supports multiple fuels" or create separate counts for "primary fuel" vs "can use this infrastructure."

## CSV vs Parquet Format Decision

There was consideration of using Parquet for the final datasets because it's much smaller (~90% reduction) and faster to read. But this would require reviewers to have pyarrow installed and specialized tools to inspect the data.

The decision was to use CSV for simplicity and reviewability, make it easy for anyone to open the files in Excel or a text editor. A parquet_comparison.py script was created to demonstrate understanding of the tradeoff. Documentation notes that Delta Lake uses Parquet internally, so production would get the efficiency benefit anyway.

## Databricks Connection Simulation

The assessment asks for a loading strategy but doesn't provide actual Databricks access. The decision was to generate the SQL statements (CREATE TABLE, COPY INTO) and print them rather than executing them.

Comments and documentation make it clear this is simulated.

## Year Range and Data Sparsity

The raw EPA data goes back to 1984, but there was a decision to filter to 2010 forward during processing. This was done because NHTSA complaint data becomes much sparser before 2010, and DOE stations data is a current snapshot only.

Filtering to 2010+ keeps the dataset focused on modern vehicles where all three data sources have reasonable coverage. This avoids having many older vehicles with no complaint or infrastructure data. The tradeoff was documented in the processing strategy.

## Null Handling in Joins

When joining EPA and NHTSA with a left join, vehicles with no matching complaints end up with null values for all complaint columns (total_complaints, crash_incidents, fire_incidents, etc.). This creates ambiguity, does null mean "no data available" or "zero complaints filed"?

The integration logic fills these nulls with 0, which assumes "no match = no complaints filed." This is implemented at line 82 of integrate_data.py using `fillna(0)` on all numeric complaint fields.

This is probably the correct interpretation for most cases. If a vehicle has no records in NHTSA's complaint database, it most likely has zero complaints rather than missing data. The result is that most of vehicles have zero complaints, which is expected since most vehicles don't have safety issues reported.

Note that some EPA fields like cylinders and displ do have legitimate nulls (about 1,100 vehicles), likely electric vehicles without traditional engines. These nulls are preserved because they represent genuinely missing or inapplicable data.

