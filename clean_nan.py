import pandas as pd
import numpy as np

# Read the CSV file
df = pd.read_csv('stock_data.csv')

print(f"Initial shape: {df.shape}")
print(f"\nMissing values per column:")
print(df.isnull().sum())

# Convert Date to datetime
df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')
df = df.sort_values('Date').reset_index(drop=True)

# Remove rows with any NaN values
initial_rows = len(df)
df = df.dropna()
removed_rows = initial_rows - len(df)

print(f"\nRows with NaN values removed: {removed_rows}")
print(f"Final shape: {df.shape}")

# Convert date back to MM/DD/YYYY format
df['Date'] = df['Date'].dt.strftime('%m/%d/%Y')

# Save the cleaned data
df.to_csv('stock_data.csv', index=False)

print(f"\n✅ Data cleaned and saved!")
print(f"Date range: {df['Date'].iloc[0]} to {df['Date'].iloc[-1]}")
print(f"Final row count: {len(df)}")
