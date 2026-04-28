import pandas as pd
import numpy as np

class SMCStrategy:
    """Smart Money Concepts Trading Strategy"""
    
    @staticmethod
    def find_order_blocks(df, lookback=5):
        """
        Identify order blocks (areas where smart money entered)
        Order blocks are areas of strong selling or buying pressure
        """
        bullish_blocks = []
        bearish_blocks = []
        
        for i in range(lookback, len(df) - lookback):
            # Bearish order block: strong down move followed by reversal
            if (df['Close'].iloc[i-lookback:i].min() < df['Close'].iloc[i] and 
                df['Close'].iloc[i:i+lookback].max() > df['Close'].iloc[i]):
                bearish_blocks.append(df['Close'].iloc[i-lookback:i].max())
            
            # Bullish order block: strong up move followed by reversal
            if (df['Close'].iloc[i-lookback:i].max() > df['Close'].iloc[i] and 
                df['Close'].iloc[i:i+lookback].min() < df['Close'].iloc[i]):
                bullish_blocks.append(df['Close'].iloc[i-lookback:i].min())
        
        return {
            'bullish': sorted(list(set([round(b, 2) for b in bullish_blocks])), reverse=True)[:5],
            'bearish': sorted(list(set([round(b, 2) for b in bearish_blocks])), reverse=True)[:5]
        }
    
    @staticmethod
    def find_liquidity_levels(df, window=20):
        """
        Identify liquidity levels (recent highs and lows)
        Smart money hunts liquidity before major moves
        """
        recent_data = df.tail(window)
        
        # Support levels (recent lows)
        support_levels = []
        for i in range(1, len(recent_data)-1):
            if (recent_data['Low'].iloc[i] < recent_data['Low'].iloc[i-1] and 
                recent_data['Low'].iloc[i] < recent_data['Low'].iloc[i+1]):
                support_levels.append(recent_data['Low'].iloc[i])
        
        # Resistance levels (recent highs)
        resistance_levels = []
        for i in range(1, len(recent_data)-1):
            if (recent_data['High'].iloc[i] > recent_data['High'].iloc[i-1] and 
                recent_data['High'].iloc[i] > recent_data['High'].iloc[i+1]):
                resistance_levels.append(recent_data['High'].iloc[i])
        
        return {
            'support': sorted(support_levels, reverse=True)[:3] if support_levels else [],
            'resistance': sorted(resistance_levels, reverse=True)[:3] if resistance_levels else [],
            'liquidity_high': recent_data['High'].max(),
            'liquidity_low': recent_data['Low'].min(),
            'midpoint': (recent_data['High'].max() + recent_data['Low'].min()) / 2
        }
    
    @staticmethod
    def find_fair_value_gaps(df, lookback=5):
        """
        Fair Value Gaps (FVGs) - areas where price hasn't traded
        These are areas of imbalance that price tends to fill
        """
        bullish_fvgs = []
        bearish_fvgs = []
        
        for i in range(1, len(df) - 1):
            high_i = df['High'].iloc[i]
            low_i = df['Low'].iloc[i]
            high_prev = df['High'].iloc[i-1]
            low_prev = df['Low'].iloc[i-1]
            high_next = df['High'].iloc[i+1]
            low_next = df['Low'].iloc[i+1]
            
            # Bullish FVG: gap up
            if low_i > high_prev:
                bullish_fvgs.append((high_i + low_i) / 2)
            
            # Bearish FVG: gap down
            if high_i < low_next:
                bearish_fvgs.append((high_i + low_i) / 2)
        
        return {
            'bullish': sorted(list(set([round(f, 2) for f in bullish_fvgs])), reverse=True)[:10],
            'bearish': sorted(list(set([round(f, 2) for f in bearish_fvgs])), reverse=True)[:10]
        }
    
    @staticmethod
    def find_supply_demand_zones(df, window=10):
        """
        Identify supply (resistance) and demand (support) zones
        Based on clustering of price action
        """
        recent_data = df.tail(window * 5)
        
        # Demand zones (clusters of lows)
        demand_zones = []
        supply_zones = []
        
        for i in range(window, len(recent_data) - window):
            low_cluster = recent_data['Low'].iloc[i-window:i].std()
            high_cluster = recent_data['High'].iloc[i-window:i].std()
            
            if low_cluster < recent_data['Close'].mean() * 0.01:  # Low volatility in lows
                demand_zones.append(recent_data['Low'].iloc[i-window:i].mean())
            
            if high_cluster < recent_data['Close'].mean() * 0.01:  # Low volatility in highs
                supply_zones.append(recent_data['High'].iloc[i-window:i].mean())
        
        return {
            'demand_zones': sorted(list(set([round(z, 2) for z in demand_zones])), reverse=True)[:3],
            'supply_zones': sorted(list(set([round(z, 2) for z in supply_zones])), reverse=True)[:3]
        }
    
    @staticmethod
    def find_ict_stdev_levels(df, window=20):
        """
        Calculates ICT Standard Deviation projections using custom Fibonacci levels.
        Identifies recent swing (high to low, or low to high) and projects the standard
        deviation extensions used in ICT analysis (-1, -1.5, -2, -2.25, -2.5, -4, -4.25).
        """
        if len(df) < window:
            return {}
            
        recent_data = df.tail(window)
        high_price = recent_data['High'].max()
        low_price = recent_data['Low'].min()
        
        high_idx = recent_data['High'].idxmax()
        low_idx = recent_data['Low'].idxmin()
        
        swing_range = high_price - low_price
        if swing_range <= 0:
            return {}
            
        # Target standard deviation levels
        fib_levels = [1, 1.5, 2, 2.25, 2.5, 4, 4.25, 4.5]
        
        projections = {
            'swing_high': high_price,
            'swing_low': low_price,
            'levels': {}
        }
        
        # If High occurred before Low, price is moving down (bearish swing)
        # SD extensions will project underneath the Low as downside liquidity targets
        if high_idx < low_idx:
            projections['direction'] = 'bearish'
            for level in fib_levels:
                projections['levels'][f"-{level}"] = low_price - (swing_range * level)
                
        # If Low occurred before High, price is moving up (bullish swing)
        # SD extensions project above the High as upside liquidity targets
        else:
            projections['direction'] = 'bullish'
            for level in fib_levels:
                projections['levels'][f"+{level}"] = high_price + (swing_range * level)
                
        return projections
    
    @staticmethod
    def generate_smc_signal(df):
        """
        Generate trading signal based on SMC concepts
        """
        # Validate input data
        if df is None or df.empty or len(df) < 10:
            return {'action': 'HOLD', 'confidence': 0, 'reason': 'Insufficient data for SMC analysis'}

        if 'Close' not in df.columns:
            return {'action': 'HOLD', 'confidence': 0, 'reason': 'Missing Close price data'}

        try:
            current_price = df['Close'].iloc[-1]

            # Get SMC levels
            liquidity = SMCStrategy.find_liquidity_levels(df)
            fvgs = SMCStrategy.find_fair_value_gaps(df)
            sd_zones = SMCStrategy.find_supply_demand_zones(df)

            signal = {'action': 'HOLD', 'confidence': 0, 'reason': ''}

            # Buy signal: Price near demand zone and liquidity level
            if sd_zones.get('demand_zones') and len(sd_zones['demand_zones']) > 0:
                demand_zone = sd_zones['demand_zones'][0]
                if abs(current_price - demand_zone) / current_price < 0.02:
                    signal['action'] = 'BUY'
                    signal['confidence'] = 75
                    signal['reason'] = f'Price near demand zone at ${demand_zone:.2f}'

            # Sell signal: Price near supply zone
            elif sd_zones.get('supply_zones') and len(sd_zones['supply_zones']) > 0:
                supply_zone = sd_zones['supply_zones'][0]
                if abs(current_price - supply_zone) / current_price < 0.02:
                    signal['action'] = 'SELL'
                    signal['confidence'] = 75
                    signal['reason'] = f'Price near supply zone at ${supply_zone:.2f}'

            # Check liquidity levels
            if liquidity.get('support') and len(liquidity['support']) > 0:
                support_level = liquidity['support'][0]
                if current_price < support_level * 1.01 and current_price > support_level * 0.99:
                    if signal['action'] == 'HOLD':
                        signal['action'] = 'BUY'
                        signal['confidence'] = 60
                        signal['reason'] = f'At support level ${support_level:.2f}'

            if liquidity.get('resistance') and len(liquidity['resistance']) > 0:
                resistance_level = liquidity['resistance'][0]
                if current_price < resistance_level * 1.01 and current_price > resistance_level * 0.99:
                    if signal['action'] == 'HOLD':
                        signal['action'] = 'SELL'
                        signal['confidence'] = 60
                        signal['reason'] = f'At resistance level ${resistance_level:.2f}'

            # FVG fill signal
            if fvgs.get('bullish'):
                bullish_fvg_level = fvgs['bullish'][0]
                if current_price < bullish_fvg_level:
                    signal['action'] = 'BUY'
                    signal['confidence'] = 85
                    signal['reason'] = f"Bullish FVG fill opportunity at ${bullish_fvg_level:.2f}"
            
            if fvgs.get('bearish') and signal['action'] == 'HOLD':
                bearish_fvg_level = fvgs['bearish'][0]
                if current_price > bearish_fvg_level:
                    signal['action'] = 'SELL'
                    signal['confidence'] = 85
                    signal['reason'] = f"Bearish FVG fill opportunity at ${bearish_fvg_level:.2f}"

            return signal

        except Exception as e:
            return {'action': 'HOLD', 'confidence': 0, 'reason': f'Error in SMC analysis: {str(e)}'}
