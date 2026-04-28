import pandas as pd
import numpy as np
import yfinance as yf

class ICTStrategy:
    """Inner Circle Trader (ICT) Strategy Specifics"""
    
    @staticmethod
    def _find_recent_swing(df, window=20):
        """Helper to find the most recent swing range in the data."""
        if len(df) < window:
            return None, None, None, None, None
            
        recent_data = df.tail(window)
        high_price = recent_data['High'].max()
        low_price = recent_data['Low'].min()
        
        high_idx = recent_data['High'].idxmax()
        low_idx = recent_data['Low'].idxmin()
        
        swing_range = high_price - low_price
        
        # Determine swing direction
        # If High occurred before Low, the impulsive swing is bearish (downward)
        direction = 'bearish' if high_idx < low_idx else 'bullish'
        
        return high_price, low_price, swing_range, direction, recent_data

    @staticmethod
    def find_ote_fib_levels(df, window=20):
        """
        Optimal Trade Entry (OTE) Fib Retracement
        Calculates the classic 62% to 79% retracement levels.
        Levels: 0.618, 0.705 (Sweet Spot), 0.79
        """
        high_price, low_price, swing_range, direction, _ = ICTStrategy._find_recent_swing(df, window)
        
        if swing_range is None or swing_range <= 0:
            return {}
            
        ote_levels = [0.5, 0.62, 0.705, 0.79, -0.5, -1, -2]
        projections = {
            'swing_high': high_price,
            'swing_low': low_price,
            'direction': direction,
            'levels': {}
        }
        
        for level in ote_levels:
            if direction == 'bearish':
                # Retracement back up after a drop or extension downwards
                price = high_price - (swing_range * level)
            else:
                # Retracement back down after a rally or extension upwards
                price = low_price + (swing_range * level)
            
            if level == 0.705:
                label = "70.5% (Sweet Spot)"
            elif level < 0:
                label = f"Target {level} Extension"
            else:
                label = f"{level*100:g}% OTE"
            
            projections['levels'][label] = price
            
        return projections

    @staticmethod
    def find_aox_fib_levels(df, window=20):
        """
        AOX Sniper Fib levels based on specific standard deviations:
        -0.21, -0.255, -0.29 (Negative Extensions)
        1.47, 1.55, 2.56, 2.6, 2.64 (Positive Extensions)
        """
        high_price, low_price, swing_range, direction, _ = ICTStrategy._find_recent_swing(df, window)
        
        if swing_range is None or swing_range <= 0:
            return {}
            
        aox_levels = [-0.21, -0.255, -0.29, 0.25, 0.5, 0.7, 1.47, 1.55, 2.56, 2.6, 2.64]
        
        projections = {
            'swing_high': high_price,
            'swing_low': low_price,
            'direction': direction,
            'levels': {}
        }
        
        # Typical retracement logic applies:
        # Range is High(0) to Low(1) or vice versa. We multiply the range by the AOX level.
        for level in aox_levels:
            if direction == 'bearish':
                # High is 0, Low is 1
                price = high_price - (swing_range * level)
            else:
                # Low is 0, High is 1
                price = low_price + (swing_range * level)
                
            # Classify meaning roughly by level value
            if level < 0:
                cat = "Target / Reversal"
            elif level < 1:
                cat = "Inner Retracement"
            else:
                cat = "Extension Target"
                
            projections['levels'][f"AOX {level} ({cat})"] = price
            
        return projections

    @staticmethod
    def find_standard_deviation_levels(df, window=20):
        """
        Calculates Standard ICT Standard Deviation projections.
        Target standard deviation levels: -1, -1.5, -2, -2.25, -2.5, -4, -4.25, -4.5
        """
        high_price, low_price, swing_range, direction, _ = ICTStrategy._find_recent_swing(df, window)
        
        if swing_range is None or swing_range <= 0:
            return {}
            
        fib_levels = [1, 1.5, 2, 2.25, 2.5, 4, 4.25, 4.5]
        
        projections = {
            'swing_high': high_price,
            'swing_low': low_price,
            'direction': direction,
            'levels': {}
        }
        
        if direction == 'bearish':
            for level in fib_levels:
                projections['levels'][f"-{level}"] = low_price - (swing_range * level)
        else:
            for level in fib_levels:
                projections['levels'][f"+{level}"] = high_price + (swing_range * level)
                
        return projections

    @staticmethod
    def calculate_midnight_setup(symbol):
        """
        Calculates the Midnight (London Open Killzone) Setup:
        - Checks local tv_live_cache for 1-minute data.
        - Falls back to yfinance if cache is missing.
        - Isolates strictly 12:01 AM to 12:29 AM in New York Time (UTC-4).
        """
        try:
            import os
            cache_file = f"tv_live_cache/{symbol}_1m.csv"
            hist = pd.DataFrame()

            if os.path.exists(cache_file):
                try:
                    hist = pd.read_csv(cache_file, index_col=0, parse_dates=True)
                    # Convert TV columns (lower) to Title Case for strategy consistency
                    if 'close' in hist.columns:
                        hist = hist.rename(columns={
                            'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'
                        })
                    # TV data is usually UTC, convert to NY
                    if hist.index.tz is None:
                        hist.index = hist.index.tz_localize('UTC')
                    hist.index = hist.index.tz_convert('America/New_York')
                except:
                    pass

            if hist.empty:
                # Disable yfinance fallback for metals/commodities as it is currently unstable
                metal_list = ['GOLD', 'XAUUSD', 'SILVER', 'XAGUSD', 'PLATINUM', 'XPTUSD', 'COPPER', 'XCUUSD']
                if symbol.upper() in metal_list:
                    return {"error": f"TradingView data not found in cache for {symbol}. Try reloading."}

                # Fallback to yfinance only for Stocks/Crypto
                yf_symbol = symbol
                if symbol == 'BTC': yf_symbol = 'BTC-USD'
                
                try:
                    ticker = yf.Ticker(yf_symbol)
                    hist = ticker.history(period="5d", interval="1m")
                    if not hist.empty:
                        hist.index = hist.index.tz_convert('America/New_York')
                except:
                    pass
            
            if hist.empty:
                return {"error": "No 1-minute data available for this symbol."}
            
            unique_dates = pd.Series(hist.index.date).unique()[::-1]
            valid_window = None
            operating_date = None
            killzone_name = "Midnight Killzone (12:01-12:29 AM)"
            
            # Find the most recent day containing our targeted window
            for d in unique_dates:
                day_data = hist[hist.index.date == d]
                
                # Try Midnight Killzone first (London Open UTC-4) (Forex, Crypto, Futures etc.)
                window_data = day_data.between_time('00:01', '00:29')
                
                # If market was closed at midnight (e.g. US Equities), fallback to New York Open Killzone
                if window_data.empty:
                    window_data = day_data.between_time('09:31', '09:59')
                    if not window_data.empty:
                        killzone_name = "NY Open Killzone (09:31-09:59 AM)"
                        
                if not window_data.empty:
                    valid_window = window_data
                    operating_date = d
                    break
                    
            if valid_window is None or valid_window.empty:
                return {"error": "Could not identify any valid midnight (00:01-00:29) or NY open (09:31-09:59) window in recent data."}
                
            # Identify core dealing range limits
            max_high = valid_window['High'].max()
            min_low = valid_window['Low'].min()
            range_diff = max_high - min_low
            
            # Find the First Fair Value Gap (FVG) in this window
            first_fvg = None
            fvg_type = None
            fvg_time = None
            # Need at least 3 candles to determine FVG
            for i in range(1, len(valid_window) - 1):
                prev_h = valid_window['High'].iloc[i-1]
                prev_l = valid_window['Low'].iloc[i-1]
                next_h = valid_window['High'].iloc[i+1]
                next_l = valid_window['Low'].iloc[i+1]
                curr_c = valid_window.iloc[i]
                
                # Bullish FVG
                if prev_h < next_l:
                    fvg_type = "Bullish"
                    first_fvg = (prev_h + next_l) / 2
                    fvg_time = valid_window.index[i].strftime('%H:%M')
                    break
                # Bearish FVG
                elif prev_l > next_h:
                    fvg_type = "Bearish"
                    first_fvg = (prev_l + next_h) / 2
                    fvg_time = valid_window.index[i].strftime('%H:%M')
                    break
                    
            # Calculate standard deviation extensions from extreme levels
            sd_factors = [1, 1.5, 2, 2.5, 3, 4]
            buy_targets = {}
            sell_targets = {}
            
            if range_diff > 0:
                for sd in sd_factors:
                    # Upward extensions from High
                    buy_targets[f"+{sd} SD"] = max_high + (range_diff * sd)
                    # Downward extensions from Low
                    sell_targets[f"-{sd} SD"] = min_low - (range_diff * sd)
                    
            return {
                "date": str(operating_date),
                "high": max_high,
                "low": min_low,
                "range": range_diff,
                "fvg_type": fvg_type,
                "fvg_price": first_fvg,
                "fvg_time": fvg_time,
                "buy_targets": buy_targets,
                "sell_targets": sell_targets,
                "killzone_name": killzone_name,
                "chart_data": valid_window.to_json(date_format='iso'),
                "full_day_data": day_data.to_json(date_format='iso') if 'day_data' in locals() else None
            }
            
        except Exception as e:
            return {"error": f"Exception calculating midnight setup: {str(e)}"}
