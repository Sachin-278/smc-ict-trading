import pandas as pd

# Read and properly sort the CSV file
df = pd.read_csv('stock_data.csv')
df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')
df = df.sort_values('Date').reset_index(drop=True)
df['Date'] = df['Date'].dt.strftime('%m/%d/%Y')

# Save back to CSV
df.to_csv('stock_data.csv', index=False)
print(f"✅ CSV file cleaned and sorted!")
print(f"Total rows: {len(df)}")
print(f"Date range: {df['Date'].iloc[0]} to {df['Date'].iloc[-1]}")
print(f"\nLast 5 entries:")
print(df.tail())
