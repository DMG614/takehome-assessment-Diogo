# Data Format Decision: CSV vs Parquet

## Decision

It was decided to use **CSV files** for the intermediate and final datasets, with the note that Parquet would be the preferred option in a production setup.

## Why Parquet is Generally Better

Parquet is a columnar storage format optimized for big data:
- **~90% smaller file sizes** (see `scripts/parquet_comparison.py`)
- Much faster reads for analytical workloads
- Better compression and encoding
- Schema stored inside the file
- Widely used in modern data lake systems

## Why CSV Was Chosen for This Assessment

### Easy to Review
CSV files can be opened directly in Excel or text editors, for example. This makes it easy for reviewers to quickly inspect data quality without needing additional tools.

### Simple for a Small Dataset
For datasets of ~20K rows, the performance difference is negligible (milliseconds). CSV keeps the pipeline straightforward without adding format conversion complexity.

## Connection to Delta Lake

The data loading strategy (see `docs/data_loading_strategy.md`) proposes **Databricks Delta Lake** as the final target. Delta Lake uses **Parquet format internally**, combined with a transaction log for ACID guarantees.

So while intermediate files are CSV, the production destination would automatically benefit from Parquet efficiency, because When CSV files are loaded into Delta Lake using the `COPY INTO` command (as shown in `scripts/load_data.py`), Delta Lake doesn't just copy the CSV format, it **converts and stores the data as Parquet files**. The transaction log (JSON files) then tracks these Parquet files.

So the data flow is: CSV (staging) → Delta Lake converts → Parquet (storage)

This means we get the best of both worlds:
- CSV files remain easy to review during development
- Final storage automatically gets Parquet's compression and query performance
- No extra conversion step needed in our pipeline

## What Would Change for Parquet

Switching to Parquet would require minimal changes, for example:

**Integration step** (`scripts/integrate_data.py`):
```python
# Change from:
df.to_csv('data/integrated/analysis.csv', index=False)
# To:
df.to_parquet('data/integrated/analysis.parquet', index=False)
```

**Loading and validation scripts**:
```python
# Change from:
df = pd.read_csv('data/integrated/analysis.csv')
# To:
df = pd.read_parquet('data/integrated/analysis.parquet')
```

## Tradeoffs Summary

| Aspect | CSV (Current) | Parquet (Alternative) |
|--------|---------------|----------------------|
| Reviewability | Open in Excel/text editor | Needs specialized tools |
| File size | 2.36 MB | 0.25 MB (90% smaller) |
| Read speed | Slower (row-based) | Faster (columnar) |
| Simplicity | Minimal dependencies | Requires pyarrow |
| Industry standard | Legacy format | Modern data lakes |
| Assessment fit | Easy to inspect | Extra complexity |

## Summary

For **this assessment**, it was assumed that CSV was the right balance between simplicity and reviewability.
