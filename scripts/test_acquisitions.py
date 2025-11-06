import pandas as pd
df = pd.read_csv('data/raw/vehicles.csv', low_memory=False)  # Handles large file
print(df.head(5))  # First 5 rows
print(df.shape)    # Row/column count
print(df.columns)  # Column names