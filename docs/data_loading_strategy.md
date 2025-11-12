## Data Loading Strategy

## Overview

This document explains the strategy for loading the integrated automotive datasets into a data warehouse for analysis. The loading process uses Databricks Delta Lake as the target platform and implements a full-refresh loading pattern. 
There's no actual connection to Databricks Delta Lake, so this is a simulation.

## Target Platform: Databricks Delta Lake

### Architecture

```
CSV Files (data/integrated/)
         ↓
   Staging Area (DBFS)
         ↓
   Databricks SQL
         ↓
   Delta Lake Tables (Azure ADLS Gen2)
         ↓
   Analytics Workspace
```

## Datasets to Load

Three integrated datasets are loaded into the data warehouse:

### 1. Vehicle Complaints Analysis
- **Table Name**: `automotive_data.analytics.vehicle_complaints_analysis`
- **Source**: `data/integrated/vehicle_complaints_analysis.csv`
- **Rows**: ~21,357 vehicle-fuel combinations
- **Note**: Dual-fuel vehicles appear twice (once per fuel type)

### 2. Fuel Infrastructure Analysis
- **Table Name**: `automotive_data.analytics.fuel_infrastructure_analysis`
- **Source**: `data/integrated/fuel_infrastructure_analysis.csv`
- **Rows**: ~43 year-fuel type aggregations

### 3. Comprehensive Vehicle Analysis
- **Table Name**: `automotive_data.analytics.comprehensive_vehicle_analysis`
- **Source**: `data/integrated/comprehensive_vehicle_analysis.csv`
- **Rows**: ~21,357 vehicle-fuel combinations
- **Note**: Dual-fuel vehicles appear twice (once per fuel type)

## Loading Strategy: Full Refresh

### Approach

The loading process uses a **full refresh** strategy:

1. **Drop existing table** (if it exists)
2. **Create new table** with current schema
3. **Load all data** from CSV files
4. **Optimize table** for query performance
5. **Validate** data quality

### Why Full Refresh?

**Advantages:**
- **Simple**: No need to track changes or incremental updates
- **Reliable**: Always have complete, consistent data
- **Clean**: No risk of duplicate or stale records
- **Fast for small datasets**: Datasets are small enough (<20K records) that full reload is fast

### Alternative: Incremental Loading

For future consideration, if datasets grow large:
- **Append-only**: Add new records without updating existing ones
- **Upsert (Merge)**: Update existing records and insert new ones
- **Change Data Capture**: Track only changed records

These require tracking metadata (load timestamps, change flags) which adds complexity.

## Loading Process

### Step 1: Connect to Databricks

```python
# Connection parameters
workspace_url = "https://dbc-a1b2c3d4-e5f6.cloud.databricks.com"
catalog = "automotive_data"
schema = "analytics"
```

### Step 2: Create Tables

For each dataset, generate a CREATE TABLE statement, like this one:

```sql
CREATE OR REPLACE TABLE automotive_data.analytics.vehicle_complaints_analysis (
  year BIGINT,
  make STRING,
  model STRING,
  VClass STRING,
  drive STRING,
  cylinders DOUBLE,
  displ DOUBLE,
  primary_fuel STRING COMMENT 'Primary fuel type (semantic naming)',
  secondary_fuel STRING COMMENT 'Secondary fuel type for dual-fuel vehicles',
  fuel_used STRING COMMENT 'The specific fuel this row represents (either primary_fuel or secondary_fuel)',
  fuel_rank INT COMMENT 'Fuel priority rank: 1=primary, 2=secondary (future-proof for tri-fuel)',
  city08 BIGINT,
  highway08 BIGINT,
  comb08 BIGINT,
  co2TailpipeGpm DOUBLE,
  total_complaints DOUBLE,
  crash_incidents DOUBLE,
  fire_incidents DOUBLE,
  total_injured DOUBLE,
  total_deaths DOUBLE,
  avg_complaint_mileage DOUBLE,
  vehicle_variants BIGINT
)
USING DELTA
COMMENT 'Vehicle-fuel combinations with safety complaints. Dual-fuel vehicles appear twice.'
LOCATION 'abfss://datalake@automotivestorage.dfs.core.windows.net/analytics/vehicle_complaints_analysis'
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);
```

**Key Features:**
- **CREATE OR REPLACE**: Drops existing table and creates new one (full refresh)
- **USING DELTA**: Stores as Delta Lake format (ACID, versioning)
- **LOCATION**: Specifies Azure ADLS Gen2 path for data storage
- **TBLPROPERTIES**: Enables automatic optimization

### Step 3: Load Data

Use COPY INTO command to load CSV data:

```sql
COPY INTO automotive_data.analytics.vehicle_complaints_analysis
FROM '/dbfs/mnt/staging/vehicle_complaints_analysis.csv'
FILEFORMAT = CSV
FORMAT_OPTIONS (
  'header' = 'true',
  'inferSchema' = 'true',
  'delimiter' = ',',
  'quote' = '"',
  'escape' = '"'
)
COPY_OPTIONS (
  'mergeSchema' = 'false',
  'force' = 'true'
);
```

**Key Features:**
- **FROM**: Reads from staging area in DBFS (Databricks File System)
- **FILEFORMAT**: Specifies CSV format
- **FORMAT_OPTIONS**: Defines CSV parsing rules
- **COPY_OPTIONS**: Forces load even if table exists

### Step 4: Optimize Tables

After loading, optimize for query performance:

```sql
-- Compact small files and create indexes
OPTIMIZE automotive_data.analytics.vehicle_complaints_analysis;

-- Update table statistics for query optimization
ANALYZE TABLE automotive_data.analytics.vehicle_complaints_analysis
COMPUTE STATISTICS;
```

**Why Optimize?**
- **OPTIMIZE**: Combines small files into larger ones (faster reads)
- **ANALYZE**: Updates statistics for query planner (better execution plans)

## Error Handling

### Potential Issues

1. **File Not Found**
   - **Cause**: CSV file missing from staging area
   - **Solution**: Verify file upload completed before loading
   - **Action**: Halt loading, alert data engineer

2. **Schema Mismatch**
   - **Cause**: CSV columns don't match table schema
   - **Solution**: Regenerate CREATE TABLE from current CSV
   - **Action**: Update table definition, retry load

3. **Data Type Errors**
   - **Cause**: Invalid values (e.g., text in numeric column)
   - **Solution**: Review data processing step for issues
   - **Action**: Fix source data, rerun processing and loading

4. **Duplicate Records**
   - **Cause**: Same data loaded multiple times
   - **Solution**: Full refresh prevents this (drops table first)
   - **Action**: Verify no duplicate files in staging

### Rollback Strategy

If loading fails:

1. **Use Time Travel** to query previous version:
   ```sql
   SELECT * FROM automotive_data.analytics.vehicle_complaints_analysis
   VERSION AS OF 1
   ```

2. **Restore previous version**:
   ```sql
   RESTORE TABLE automotive_data.analytics.vehicle_complaints_analysis
   TO VERSION AS OF 1
   ```

3. **Investigate issue**, fix, and retry load


## Summary

**Platform**: Databricks Delta Lake
**Strategy**: Full refresh
**Datasets**: 3 integrated tables
