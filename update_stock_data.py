import pandas as pd
from datetime import datetime, timedelta
import os
import warnings
from tvDatafeed import TvDatafeed, Interval

warnings.filterwarnings('ignore')

# Symbols to update
symbols_to_update = {
    'AMZN': ('NASDAQ', 'AMZN'),
    'DPZ': ('NYSE', 'DPZ'),
    'NFLX': ('NASDAQ', 'NFLX'),
    'AAPL': ('NASDAQ', 'AAPL'),
    'XAUUSD': ('OANDA', 'XAUUSD'),
    'XAGUSD': ('OANDA', 'XAGUSD'),
    'XPTUSD': ('OANDA', 'XPTUSD'),
    'BTC': ('BINANCE', 'BTCUSDT')
}

csv_file = 'stock_data.csv'

def update_data():
    print("Starting data update from TradingView...")
    tv = TvDatafeed()
    
    # Read existing data
    if os.path.exists(csv_file):
        existing_df = pd.read_csv(csv_file)
        existing_df['Date'] = pd.to_datetime(existing_df['Date'])
        print(f"Loaded existing data with {len(existing_df)} rows.")
    else:
        existing_df = pd.DataFrame()
        print("No existing data found. Creating new file.")

    all_new_data = {}
    
    for app_symbol, (exchange, tv_symbol) in symbols_to_update.items():
        print(f"Fetching {app_symbol} ({tv_symbol})...")
        try:
            df = tv.get_hist(symbol=tv_symbol, exchange=exchange, interval=Interval.in_daily, n_bars=100)
            if df is not None and not df.empty:
                # tvDatafeed returns 'close' (lowercase)
                all_new_data[app_symbol] = df['close']
                print(f"  Successfully fetched {len(df)} days of data.")
            else:
                print(f"  Warning: No data returned for {app_symbol}")
        except Exception as e:
            print(f"  Error fetching {app_symbol}: {e}")

    if not all_new_data:
        print("No data was fetched. Exiting.")
        return

    # Create new DataFrame
    new_df = pd.DataFrame(all_new_data)
    new_df.index.name = 'Date'
    new_df = new_df.reset_index()
    new_df['Date'] = pd.to_datetime(new_df['Date'])

    # Combine
    if not existing_df.empty:
        combined = pd.concat([existing_df, new_df]).drop_duplicates(subset=['Date'], keep='last')
        combined = combined.sort_values('Date').reset_index(drop=True)
    else:
        combined = new_df

    # Save
    combined.to_csv(csv_file, index=False)
    print(f"\nSuccessfully updated {csv_file}")
    print(f"Latest Date: {combined['Date'].max().date()}")

if __name__ == "__main__":
    update_data()
