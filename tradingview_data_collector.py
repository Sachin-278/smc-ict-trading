import pandas as pd
import numpy as np
from datetime import datetime
import time
import os
import warnings
from tvDatafeed import TvDatafeed, Interval

warnings.filterwarnings('ignore')

class TradingViewDataCollector:
    """
    Data collector using tvdatafeed to fetch real-time data from TradingView
    """

    def __init__(self):
        # Initialize TV Datafeed (Anonymous)
        self.tv = TvDatafeed()
        
        # Symbol mapping for TradingView (Exchange, Symbol)
        self.tv_mapping = {
            # US Stocks
            'AMZN': ('NASDAQ', 'AMZN'),
            'DPZ': ('NYSE', 'DPZ'),
            'NFLX': ('NASDAQ', 'NFLX'),
            'AAPL': ('NASDAQ', 'AAPL'),
            'GOOGL': ('NASDAQ', 'GOOGL'),
            'MSFT': ('NASDAQ', 'MSFT'),
            'TSLA': ('NASDAQ', 'TSLA'),
            'NVDA': ('NASDAQ', 'NVDA'),
            
            # Indian Stocks
            'RELIANCE': ('NSE', 'RELIANCE'),
            'TCS': ('NSE', 'TCS'),
            'HDFCBANK': ('NSE', 'HDFCBANK'),
            'ICICIBANK': ('NSE', 'ICICIBANK'),
            'INFY': ('NSE', 'INFY'),
            'BAJFINANCE': ('NSE', 'BAJFINANCE'),
            'HINDUNILVR': ('NSE', 'HINDUNILVR'),
            'ITC': ('NSE', 'ITC'),
            'KOTAKBANK': ('NSE', 'KOTAKBANK'),
            'LT': ('NSE', 'LT'),
            
            # Forex
            'EURUSD': ('FX_IDC', 'EURUSD'),
            'GBPUSD': ('FX_IDC', 'GBPUSD'),
            'USDJPY': ('FX_IDC', 'USDJPY'),
            'USDCHF': ('FX_IDC', 'USDCHF'),
            'AUDUSD': ('FX_IDC', 'AUDUSD'),
            'USDCAD': ('FX_IDC', 'USDCAD'),
            'NZDUSD': ('FX_IDC', 'NZDUSD'),
            'EURJPY': ('FX_IDC', 'EURJPY'),
            'GBPJPY': ('FX_IDC', 'GBPJPY'),
            
            # Metals & Commodities
            'XAUUSD': ('OANDA', 'XAUUSD'),
            'XAGUSD': ('OANDA', 'XAGUSD'),
            'XCUUSD': ('COMEX', 'HG1!'),
            'XPTUSD': ('OANDA', 'XPTUSD'),
            'GOLD': ('COMEX', 'GC1!'),
            'SILVER': ('COMEX', 'SI1!'),
            'WTI_CRUDE': ('NYMEX', 'CL1!'),
            'BRENT_CRUDE': ('ICE', 'BRN1!'),
            
            # Crypto
            'BTC': ('BINANCE', 'BTCUSDT'),
            'ETH': ('BINANCE', 'ETHUSDT'),
            'BNB': ('BINANCE', 'BNBUSDT'),
            'ADA': ('BINANCE', 'ADAUSDT'),
            'SOL': ('BINANCE', 'SOLUSDT')
        }

        self.cache_dir = 'tv_live_cache'
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def fetch_tv_data(self, symbol, interval=Interval.in_1_hour, n_bars=500):
        """Fetch data from TradingView"""
        try:
            if symbol not in self.tv_mapping:
                print(f"Symbol {symbol} not in TV mapping, trying default NASDAQ")
                exchange, tv_symbol = 'NASDAQ', symbol
            else:
                exchange, tv_symbol = self.tv_mapping[symbol]
            
            print(f"Fetching {symbol} ({exchange}:{tv_symbol}) at {interval} interval...")
            df = self.tv.get_hist(symbol=tv_symbol, exchange=exchange, interval=interval, n_bars=n_bars)
            
            if df is not None and not df.empty:
                return df
            return None
        except Exception as e:
            print(f"Error fetching {symbol} from TV: {e}")
            return None

    def update_cache(self, symbols=None):
        """Update live cache for specified symbols and common timeframes"""
        if symbols is None:
            symbols = list(self.tv_mapping.keys())
            
        timeframes = {
            '1m': Interval.in_1_minute,
            '5m': Interval.in_5_minute,
            '15m': Interval.in_15_minute,
            '1h': Interval.in_1_hour,
            '1d': Interval.in_daily
        }
        
        for symbol in symbols:
            print(f"--- Updating Cache for {symbol} ---")
            for tf_name, tf_interval in timeframes.items():
                try:
                    df = self.fetch_tv_data(symbol, tf_interval)
                    if df is not None:
                        cache_path = os.path.join(self.cache_dir, f"{symbol}_{tf_name}.csv")
                        df.to_csv(cache_path)
                        print(f"[OK] Cached {symbol} {tf_name}")
                    else:
                        print(f"[WARN] No data for {symbol} {tf_name}")
                except Exception as e:
                    print(f"[ERROR] In {symbol} {tf_name}: {e}")
                
                time.sleep(1.0) # Increased delay to avoid rate limits

    def update_main_csv(self, csv_file='stock_data.csv'):
        """Update the main stock_data.csv with daily close prices from TV"""
        print("Updating main CSV with daily close prices...")
        
        daily_data = {}
        for symbol in self.tv_mapping.keys():
            df = self.fetch_tv_data(symbol, Interval.in_daily, n_bars=100)
            if df is not None:
                daily_data[symbol] = df['close']
        
        if not daily_data:
            return False
            
        new_df = pd.DataFrame(daily_data)
        new_df.index.name = 'Date'
        new_df = new_df.reset_index()
        
        if os.path.exists(csv_file):
            existing_df = pd.read_csv(csv_file)
            existing_df['Date'] = pd.to_datetime(existing_df['Date'])
            new_df['Date'] = pd.to_datetime(new_df['Date'])
            
            combined = pd.concat([existing_df, new_df]).drop_duplicates(subset=['Date'], keep='last')
            combined = combined.sort_values('Date')
            combined.to_csv(csv_file, index=False)
        else:
            new_df.to_csv(csv_file, index=False)
            
        print(f"Saved to {csv_file}")
        return True

def continuous_update(interval_minutes=5):
    """Loop to update data every X minutes"""
    collector = TradingViewDataCollector()
    print(f"Continuous update started. Interval: {interval_minutes} min")
    
    while True:
        try:
            start_time = time.time()
            print(f"\nCycle started: {datetime.now().strftime('%H:%M:%S')}")
            
            # 1. Update live cache (intraday)
            collector.update_cache()
            
            # 2. Update main CSV (daily)
            collector.update_main_csv()
            
            elapsed = (time.time() - start_time) / 60
            sleep_time = max(0, (interval_minutes - elapsed) * 60)
            
            print(f"Cycle complete. Sleeping for {sleep_time/60:.1f} minutes...")
            time.sleep(sleep_time)
            
        except KeyboardInterrupt:
            print("\nStopped by user")
            break
        except Exception as e:
            print(f"[ERROR] In loop: {e}")
            time.sleep(60)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--continuous', action='store_true')
    parser.add_argument('--interval', type=int, default=5)
    args = parser.parse_args()
    
    if args.continuous:
        continuous_update(args.interval)
    else:
        collector = TradingViewDataCollector()
        collector.update_cache()
        collector.update_main_csv()