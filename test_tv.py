from tvDatafeed import TvDatafeed, Interval
import pandas as pd

tv = TvDatafeed()
symbols = [
    ('NASDAQ', 'AMZN'),
    ('OANDA', 'XAUUSD'),
    ('TVC', 'XAUUSD'),
    ('SAXO', 'XAUUSD'),
    ('OANDA', 'XPTUSD'),
    ('TVC', 'PLATINUM'),
    ('SAXO', 'XPTUSD'),
    ('COMEX', 'HG1!')
]

for exchange, symbol in symbols:
    print(f"Testing {symbol} on {exchange}...")
    try:
        df = tv.get_hist(symbol=symbol, exchange=exchange, interval=Interval.in_1_minute, n_bars=10)
        if df is not None and not df.empty:
            print(f"  SUCCESS: Fetched {len(df)} rows. Last Close: {df['close'].iloc[-1]}")
        else:
            print(f"  FAILED: No data returned.")
    except Exception as e:
        print(f"  ERROR: {e}")
