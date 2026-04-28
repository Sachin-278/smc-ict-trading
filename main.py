import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error
import plotly.graph_objects as go
import yfinance as yf
import warnings
warnings.filterwarnings('ignore')
from smc_strategy import SMCStrategy
from ict_strategy import ICTStrategy
from tradingview_integration import create_tradingview_embed, create_tradingview_mini_chart
import io
import os
from streamlit_autorefresh import st_autorefresh
from tvDatafeed import TvDatafeed, Interval

# Auto-refresh every 5 minutes
st_autorefresh(interval=5 * 60 * 1000, key="datarefresh")

st.set_page_config(page_title="Stock Price Prediction", layout="wide")

# Load historical data
data = pd.read_csv('stock_data.csv', parse_dates=['Date'])
data.set_index('Date', inplace=True)

# Asset categories
asset_categories = {
    "🇺🇸 US Stocks": ['AMZN', 'DPZ', 'NFLX', 'AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA'],
    "🇮🇳 Indian Stocks": ['RELIANCE', 'TCS', 'HDFCBANK', 'ICICIBANK', 'INFY', 'BAJFINANCE', 'HINDUNILVR', 'ITC', 'KOTAKBANK', 'LT'],
    "💱 Forex": ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD', 'EURJPY', 'GBPJPY'],
    "🏭 Metals & Commodities": ['XAUUSD', 'XAGUSD', 'XCUUSD', 'XPTUSD', 'WTI_CRUDE', 'BRENT_CRUDE'],
    "₿ Crypto": ['BTC', 'ETH', 'BNB', 'ADA', 'SOL']
}

# Map displayed metal symbols to internal data column names in stock_data.csv
symbol_to_data_column = {
    'XAUUSD': 'GOLD',
    'XAGUSD': 'SILVER',
    'XCUUSD': 'COPPER',
    'XPTUSD': 'PLATINUM'
}

def get_data_column(symbol):
    return symbol_to_data_column.get(symbol, symbol)

# Flatten all options for the main selectbox
all_options = []
for category, symbols in asset_categories.items():
    all_options.extend(symbols)

# Select target with categories
st.sidebar.header("🎯 Asset Selection")

# Initialize TV Datafeed (Cached for performance)
@st.cache_resource
def get_tv_connection():
    return TvDatafeed()

def refresh_tv_cache(symbol, interval_str):
    """Update local cache file for a symbol and interval if needed"""
    cache_dir = "tv_live_cache"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
        
    cache_file = f"{cache_dir}/{symbol}_{interval_str}.csv"
    
    # Check if update is needed (every 5 minutes)
    needs_update = True
    if os.path.exists(cache_file):
        mtime = os.path.getmtime(cache_file)
        if (datetime.now().timestamp() - mtime) < 300: # 5 minutes
            needs_update = False
            
    if needs_update:
        try:
            tv = get_tv_connection()
            # Expanded mapping for all metals, commodities and forex
            mapping = {
                # Metals (Internal & Display names)
                'XAUUSD': ('SAXO', 'XAUUSD'), 'GOLD': ('SAXO', 'XAUUSD'),
                'XAGUSD': ('OANDA', 'XAGUSD'), 'SILVER': ('OANDA', 'XAGUSD'),
                'XPTUSD': ('SAXO', 'XPTUSD'), 'PLATINUM': ('SAXO', 'XPTUSD'),
                'XCUUSD': ('COMEX', 'HG1!'), 'COPPER': ('COMEX', 'HG1!'),
                
                # US Stocks
                'AMZN': ('NASDAQ', 'AMZN'), 'AAPL': ('NASDAQ', 'AAPL'),
                'MSFT': ('NASDAQ', 'MSFT'), 'TSLA': ('NASDAQ', 'TSLA'),
                'NVDA': ('NASDAQ', 'NVDA'), 'GOOGL': ('NASDAQ', 'GOOGL'),
                'NFLX': ('NASDAQ', 'NFLX'), 'DPZ': ('NYSE', 'DPZ'),

                # Forex
                'EURUSD': ('FX_IDC', 'EURUSD'), 'GBPUSD': ('FX_IDC', 'GBPUSD'),
                'USDJPY': ('FX_IDC', 'USDJPY'), 'USDCHF': ('FX_IDC', 'USDCHF'),
                'AUDUSD': ('FX_IDC', 'AUDUSD'), 'USDCAD': ('FX_IDC', 'USDCAD'),
                'NZDUSD': ('FX_IDC', 'NZDUSD'), 'EURJPY': ('FX_IDC', 'EURJPY'),
                'GBPJPY': ('FX_IDC', 'GBPJPY'),

                # Crypto
                'BTC': ('BINANCE', 'BTCUSDT'), 'ETH': ('BINANCE', 'ETHUSDT'),
                'BNB': ('BINANCE', 'BNBUSDT'), 'ADA': ('BINANCE', 'ADAUSDT'),
                'SOL': ('BINANCE', 'SOLUSDT'),

                # Commodities
                'WTI_CRUDE': ('NYMEX', 'CL1!'), 'BRENT_CRUDE': ('ICE', 'BRN1!'),
                
                # Indian Stocks (NSE)
                'RELIANCE': ('NSE', 'RELIANCE'), 'TCS': ('NSE', 'TCS'),
                'HDFCBANK': ('NSE', 'HDFCBANK'), 'ICICIBANK': ('NSE', 'ICICIBANK'),
                'INFY': ('NSE', 'INFY'), 'BAJFINANCE': ('NSE', 'BAJFINANCE'),
                'HINDUNILVR': ('NSE', 'HINDUNILVR'), 'ITC': ('NSE', 'ITC'),
                'KOTAKBANK': ('NSE', 'KOTAKBANK'), 'LT': ('NSE', 'LT')
            }
            
            exchange, tv_symbol = mapping.get(symbol, ('NASDAQ', symbol))
            
            tf_tv_map = {
                '1m': Interval.in_1_minute, '5m': Interval.in_5_minute,
                '15m': Interval.in_15_minute, '1h': Interval.in_1_hour, '1d': Interval.in_daily
            }
            
            # Increase n_bars for 1m to ensure we reach midnight
            n_bars = 2000 if interval_str == '1m' else 500
            
            df = tv.get_hist(symbol=tv_symbol, exchange=exchange, 
                             interval=tf_tv_map.get(interval_str, Interval.in_1_hour), n_bars=n_bars)
            
            if df is not None and not df.empty:
                df.to_csv(cache_file)
                return True
        except Exception as e:
            print(f"TV Fetch Error: {e}")
    return False

selected_category = st.sidebar.selectbox("Select Asset Category", options=list(asset_categories.keys()))

# Get symbols for selected category
category_symbols = asset_categories[selected_category]

# Main asset selector
target_column = st.selectbox(
    f"Select {selected_category.split()[1]} for prediction",
    options=category_symbols,
    help=f"Choose from {len(category_symbols)} {selected_category.split()[1].lower()} options"
)

# Legacy Indian market option (keeping for backward compatibility)
st.sidebar.header("🇮🇳 Additional Options")
include_indian_stocks = st.sidebar.checkbox("Include NSE Stocks (Legacy)")
if include_indian_stocks:
    indian_stocks = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'INFY.NS']
    selected_indian = st.sidebar.selectbox("Select Indian Stock", options=indian_stocks)
    if selected_indian:
        target_column = selected_indian.split('.')[0]  # Use symbol name without .NS
# Dynamic feature selection based on category
if selected_category == "🇺🇸 US Stocks":
    # Use other US stocks as features for US stock prediction
    available_features = [col for col in data.columns if col in ['AMZN', 'DPZ', 'NFLX', 'AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA'] and col != target_column]
    X = data[available_features[:3]]  # Use first 3 available features
elif selected_category == "🇮🇳 Indian Stocks":
    # Use other Indian stocks as features
    available_features = [col for col in data.columns if col in ['RELIANCE', 'TCS', 'HDFCBANK', 'ICICIBANK', 'INFY', 'BAJFINANCE', 'HINDUNILVR', 'ITC', 'KOTAKBANK', 'LT'] and col != target_column]
    X = data[available_features[:3]] if len(available_features) >= 3 else data[['AMZN', 'DPZ', 'BTC']]  # Fallback to US stocks
elif selected_category == "💱 Forex":
    # Use other forex pairs as features
    available_features = [col for col in data.columns if col in ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD', 'EURJPY', 'GBPJPY'] and col != target_column]
    X = data[available_features[:3]] if len(available_features) >= 3 else data[['AMZN', 'DPZ', 'BTC']]  # Fallback
elif selected_category == "🏭 Metals & Commodities":
    # Use other metals/commodities as features
    metals_data_columns = [get_data_column(sym) for sym in ['XAUUSD', 'XAGUSD', 'XCUUSD', 'XPTUSD', 'WTI_CRUDE', 'BRENT_CRUDE']]
    available_features = [col for col in data.columns if col in metals_data_columns and col != get_data_column(target_column)]
    X = data[available_features[:3]] if len(available_features) >= 3 else data[['AMZN', 'DPZ', 'BTC']]  # Fallback
elif selected_category == "₿ Crypto":
    # Use other crypto as features
    available_features = [col for col in data.columns if col in ['BTC', 'ETH', 'BNB', 'ADA', 'SOL'] and col != target_column]
    X = data[available_features[:3]] if len(available_features) >= 3 else data[['AMZN', 'DPZ', 'NFLX']]  # Fallback
else:
    # Default fallback
    X = data[['DPZ', 'BTC', 'NFLX']]

# Ensure target column exists
data_target_column = get_data_column(target_column)
if data_target_column not in data.columns:
    st.error(f"❌ Target column '{target_column}' not found in data. Available columns: {list(data.columns)}")
    st.stop()

y = data[data_target_column]

# Remove NaN values
valid_idx = ~(X.isnull().any(axis=1) | y.isnull())
X = X[valid_idx]
y = y[valid_idx]

# Split data
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Model performance
val_predictions = model.predict(X_val)
mse = mean_squared_error(y_val, val_predictions)
rmse = np.sqrt(mse)
mape = mean_absolute_percentage_error(y_val, val_predictions)

# ==================== LIVE TRADING SECTION ====================
st.sidebar.header("⚡ LIVE TRADING FORECASTING")

# Yahoo Finance symbol mapping for live data
yahoo_mapping = {
    'AMZN': 'AMZN', 'DPZ': 'DPZ', 'NFLX': 'NFLX', 'AAPL': 'AAPL', 'GOOGL': 'GOOGL',
    'MSFT': 'MSFT', 'TSLA': 'TSLA', 'NVDA': 'NVDA',
    'RELIANCE': 'RELIANCE.NS', 'TCS': 'TCS.NS', 'HDFCBANK': 'HDFCBANK.NS',
    'ICICIBANK': 'ICICIBANK.NS', 'INFY': 'INFY.NS', 'BAJFINANCE': 'BAJFINANCE.NS',
    'HINDUNILVR': 'HINDUNILVR.NS', 'ITC': 'ITC.NS', 'KOTAKBANK': 'KOTAKBANK.NS', 'LT': 'LT.NS',
    'EURUSD': 'EURUSD=X', 'GBPUSD': 'GBPUSD=X', 'USDJPY': 'USDJPY=X', 'USDCHF': 'USDCHF=X',
    'AUDUSD': 'AUDUSD=X', 'USDCAD': 'USDCAD=X', 'NZDUSD': 'NZDUSD=X', 'EURJPY': 'EURJPY=X', 'GBPJPY': 'GBPJPY=X',
    'XAUUSD': 'XAUUSD=X', 'XAGUSD': 'XAGUSD=X', 'XCUUSD': 'HG=F', 'XPTUSD': 'XPTUSD=X',
    'WTI_CRUDE': 'CL=F', 'BRENT_CRUDE': 'BZ=F',
    'BTC': 'BTC-USD', 'ETH': 'ETH-USD', 'BNB': 'BNB-USD', 'ADA': 'ADA-USD', 'SOL': 'SOL-USD'
}

# Fetch live data
@st.cache_data(ttl=60)
def get_live_data(symbol):
    """Fetch live stock data from TradingView cache or yfinance"""
    try:
        # First try TV Cache
        refresh_tv_cache(symbol, '1d')
        cache_file = f"tv_live_cache/{symbol}_1d.csv"
        
        if os.path.exists(cache_file):
            df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            if not df.empty:
                # TV returns 'close' (lower)
                price_col = 'close' if 'close' in df.columns else 'Close'
                if price_col in df.columns:
                    price = df[price_col].iloc[-1]
                    avg = df[price_col].tail(50).mean()
                    return price, avg
        
        # Metal/Commodity Check
        metal_list = ['GOLD', 'XAUUSD', 'SILVER', 'XAGUSD', 'PLATINUM', 'XPTUSD', 'COPPER', 'XCUUSD', 'WTI_CRUDE', 'BRENT_CRUDE']
        if symbol.upper() in metal_list:
            return None, None
            
        # Fallback to yfinance only for non-metal assets
        yahoo_symbol = yahoo_mapping.get(symbol, symbol)
        ticker = yf.Ticker(yahoo_symbol)
        hist = ticker.history(period='1y')
        if len(hist) > 0:
            return hist['Close'].iloc[-1], hist['Close'].iloc[-50:].mean()
        
        return None, None
    except Exception as e:
        # Log to console for dev
        print(f"Live Data Fetch Error for {symbol}: {e}")
        return None, None

# Get current prices for category symbols
current_prices = {}
ma50 = {}
category_symbols_for_live = asset_categories[selected_category][:4]  # Show first 4 symbols

for stock in category_symbols_for_live:
    price, avg = get_live_data(stock)
    current_prices[stock] = price
    ma50[stock] = avg

# Display live prices in sidebar
st.sidebar.subheader(f"💰 Live {selected_category.split()[1]} Prices")
price_cols = st.sidebar.columns(2)
for i, stock in enumerate(category_symbols_for_live):
    with price_cols[i % 2]:
        if current_prices[stock]:
            # Format based on asset type
            if selected_category == "💱 Forex":
                st.metric(stock, f"{current_prices[stock]:.4f}")
            elif selected_category in ["🏭 Metals & Commodities", "₿ Crypto"]:
                st.metric(stock, f"${current_prices[stock]:.2f}")
            else:  # Stocks
                st.metric(stock, f"${current_prices[stock]:.2f}")
        else:
            st.warning(f"No data for {stock}")

# Trading settings
st.sidebar.subheader("⚙️ Trading Settings")
confidence_threshold = st.sidebar.slider("Confidence Threshold (%)", 50, 100, 75)
position_size = st.sidebar.slider("Position Size (%)", 1, 100, 50)

# ==================== MAIN CONTENT ====================
st.title(f"🚀 {target_column} Stock Price Prediction & Live Trading")

# Create tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["📊 Forecast", "💹 Live Trading Signals", "📈 Technical Analysis", "🎯 SMC Strategy", "📺 TradingView Charts", "📋 Model Performance", "🎯 ICT AOX Strategy"])

with tab1:
    st.header(f"{target_column} Price Forecast")
    
    # Forecast settings
    max_forecast_days = len(X)
    future_days = st.slider(f"Forecast Days (1-{max_forecast_days})", min_value=1, max_value=max_forecast_days, value=min(7, max_forecast_days))
    
    # Generate predictions
    last_known_date = data.index[-1]
    future_dates = [last_known_date + timedelta(days=i) for i in range(1, future_days + 1)]
    future_predictions = model.predict(X.tail(future_days))
    
    # Calculate trend
    recent_price = y.iloc[-1]
    avg_prediction = future_predictions.mean()
    trend = "📈 BULLISH" if avg_prediction > recent_price else "📉 BEARISH"
    confidence = min(100, abs((avg_prediction - recent_price) / recent_price * 100) + 70)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Current Price", f"${recent_price:.2f}")
    with col2:
        st.metric("Avg Forecast", f"${avg_prediction:.2f}")
    with col3:
        st.metric("Trend", trend)
    with col4:
        st.metric("Confidence", f"{confidence:.1f}%")
    
    # Plot
    fig = go.Figure()
    
    # Show entire history
    historical_data = data[data_target_column].dropna()
    
    # Synthesize OHLC for candlesticks
    open_prices = historical_data.shift(1).fillna(historical_data)
    volatility = historical_data.pct_change().std() if len(historical_data) > 1 else 0
    high_prices = historical_data.combine(open_prices, max) * (1 + volatility * 0.5)
    low_prices = historical_data.combine(open_prices, min) * (1 - volatility * 0.5)
    
    fig.add_trace(go.Candlestick(
        x=historical_data.index,
        open=open_prices,
        high=high_prices,
        low=low_prices,
        close=historical_data,
        name='Historical'
    ))
    
    fig.add_trace(go.Scatter(
        x=future_dates,
        y=future_predictions,
        mode='lines+markers',
        name='Forecast',
        line=dict(color='red', dash='dash', width=2),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title=f"{target_column} Price Forecast (Next {future_days} Days)",
        xaxis_title="Date",
        yaxis_title="Price ($)",
        template="plotly_white",
        hovermode='x unified',
        xaxis_rangeslider_visible=False
    )
    
    st.plotly_chart(fig, width='stretch')

with tab2:
    st.header("💹 Live Trading Signals")

    # Trading logic - use symbols from current category
    signal_data = []
    # Get available symbols that have price data
    available_symbols = [stock for stock in category_symbols_for_live if stock in current_prices and current_prices[stock] is not None]

    for stock in available_symbols:
        if stock == target_column:  # Skip the target column itself
            continue

        # Simple momentum indicator
        if stock in data.columns:
            historical = data[stock].dropna()
            if len(historical) > 20:  # Need at least 20 data points
                momentum = (historical.iloc[-1] - historical.iloc[-20:].mean()) / historical.iloc[-20:].mean()

                # Generate signal based on price vs MA50
                if ma50[stock] and ma50[stock] > 0:
                    ma_signal = "BUY" if current_prices[stock] < ma50[stock] else "SELL"
                else:
                    ma_signal = "HOLD"

                # Determine action based on confidence
                confidence_score = abs(momentum) * 100
                if ma_signal == 'BUY' and confidence_score > confidence_threshold:
                    action = '✅ BUY'
                elif ma_signal == 'SELL' and confidence_score > confidence_threshold:
                    action = '❌ SELL'
                else:
                    action = '⏸️ HOLD'

                signal_data.append({
                    'Asset': stock,
                    'Price': f"${current_prices[stock]:.2f}" if selected_category in ["🇺🇸 US Stocks", "🇮🇳 Indian Stocks", "🏭 Metals & Commodities", "₿ Crypto"] else f"{current_prices[stock]:.4f}",
                    'MA50': f"${ma50[stock]:.2f}" if ma50[stock] else "N/A",
                    'Signal': ma_signal,
                    'Momentum': f"{momentum*100:.2f}%" if momentum else "N/A",
                    'Confidence': f"{confidence_score:.1f}%",
                    'Action': action
                })

    if signal_data:
        signals_df = pd.DataFrame(signal_data)
        st.dataframe(signals_df, width='stretch')

        # Trading recommendation
        buy_signals = sum(1 for row in signal_data if '✅' in row['Action'])
        sell_signals = sum(1 for row in signal_data if '❌' in row['Action'])
        st.info(f"🎯 Trading Recommendation: {buy_signals} BUY, {sell_signals} SELL signals. Position size: {position_size}%")
    else:
        st.warning("⚠️ No trading signals available. This may be due to insufficient data or market conditions.")

with tab3:
    st.header("📈 Technical Analysis")
    
    # Calculate technical indicators
    historical = data[data_target_column].dropna()
    ma_20 = historical.rolling(window=20).mean()
    ma_50 = historical.rolling(window=50).mean()
    
    fig_ta = go.Figure()
    
    # Price and moving averages
    fig_ta.add_trace(go.Scatter(x=historical.index, y=historical, mode='lines', name='Price', line=dict(color='blue')))
    fig_ta.add_trace(go.Scatter(x=ma_20.index, y=ma_20, mode='lines', name='MA20', line=dict(color='orange', dash='dash')))
    fig_ta.add_trace(go.Scatter(x=ma_50.index, y=ma_50, mode='lines', name='MA50', line=dict(color='red', dash='dash')))
    
    fig_ta.update_layout(
        title=f"{target_column} Technical Analysis - Moving Averages",
        xaxis_title="Date",
        yaxis_title="Price ($)",
        template="plotly_white",
        hovermode='x unified'
    )
    
    st.plotly_chart(fig_ta, width='stretch')
    
    # Volatility
    returns = historical.pct_change()
    volatility = returns.std() * np.sqrt(252) * 100
    st.metric("Annualized Volatility", f"{volatility:.2f}%")

with tab4:
    st.header("🎯 Smart Money Concepts (SMC) Strategy")

    # Check if we have enough data for SMC analysis
    if data_target_column not in data.columns:
        st.error(f"❌ No data available for {target_column}")
    elif len(data[data_target_column].dropna()) < 50:
        st.warning(f"⚠️ Insufficient data for SMC analysis. Need at least 50 data points, got {len(data[data_target_column].dropna())}")
    else:
        # Prepare data for SMC analysis with proper OHLC structure
        try:
            # Use the target column as Close price
            close_prices = data[data_target_column].dropna()

            # Create OHLC data by simulating High/Low from Close prices with some volatility
            # This is a simplified approach - in real trading, you'd have actual OHLC data
            volatility = close_prices.pct_change().std()
            high_prices = close_prices * (1 + volatility * 0.5)  # Simulate highs
            low_prices = close_prices * (1 - volatility * 0.5)   # Simulate lows

            data_for_smc = pd.DataFrame({
                'Close': close_prices,
                'High': high_prices,
                'Low': low_prices
            }).dropna()

            data_for_smc = pd.DataFrame({
                'Close': close_prices,
                'High': high_prices,
                'Low': low_prices
            }).dropna()

            # Additional validation
            if len(data_for_smc) < 20:
                st.warning("⚠️ Not enough data points after cleaning for SMC analysis")
            elif not all(col in data_for_smc.columns for col in ['Close', 'High', 'Low']):
                st.error("❌ Missing required OHLC columns for SMC analysis")
            else:
                # Get SMC signals
                try:
                    smc_signal = SMCStrategy.generate_smc_signal(data_for_smc)
                    order_blocks = SMCStrategy.find_order_blocks(data_for_smc)
                    liquidity = SMCStrategy.find_liquidity_levels(data_for_smc)
                    fvgs = SMCStrategy.find_fair_value_gaps(data_for_smc)
                    sd_zones = SMCStrategy.find_supply_demand_zones(data_for_smc)
                    ict_stdev = SMCStrategy.find_ict_stdev_levels(data_for_smc)

                    # Display SMC signal
                    st.subheader("📊 Current SMC Signal")
                    signal_color = {
                        'BUY': '🟢',
                        'SELL': '🔴',
                        'HOLD': '🟡'
                    }.get(smc_signal.get('action', 'HOLD'), '🟡')

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Signal", f"{signal_color} {smc_signal.get('action', 'HOLD')}")
                    with col2:
                        st.metric("Confidence", f"{smc_signal.get('confidence', 0):.1f}%")
                    with col3:
                        st.metric("Reason", smc_signal.get('reason', 'N/A'))

                    # Display SMC levels
                    st.subheader("🎯 SMC Analysis Components")

                    col1, col2 = st.columns(2)

                    with col1:
                        st.write("**Order Blocks:**")
                        if order_blocks.get('bullish'):
                            st.write("🐂 Bullish:", [f"{round(ob, 2)}" for ob in order_blocks['bullish'][:3]])
                        if order_blocks.get('bearish'):
                            st.write("🐻 Bearish:", [f"{round(ob, 2)}" for ob in order_blocks['bearish'][:3]])

                        st.write("**Liquidity Levels:**")
                        if liquidity.get('support'):
                            st.write("📈 Support:", [f"{round(l, 2)}" for l in liquidity['support'][:3]])
                        if liquidity.get('resistance'):
                            st.write("📉 Resistance:", [f"{round(l, 2)}" for l in liquidity['resistance'][:3]])

                        if ict_stdev.get('levels'):
                            st.write("**ICT Fib Extensions:**")
                            dir_emoji = "🐻 Downside Targets" if ict_stdev.get('direction') == 'bearish' else "🐂 Upside Targets"
                            st.write(f"{dir_emoji}:")
                            for lvl, val in list(ict_stdev['levels'].items())[:4]:
                                st.write(f"  • {lvl} SD: ${val:.2f}")

                    with col2:
                        st.write("**Fair Value Gaps:**")
                        if fvgs.get('bullish'):
                            st.write("🟢 Bullish FVG:", [f"{round(fvg, 2)}" for fvg in fvgs['bullish'][:3]])
                        if fvgs.get('bearish'):
                            st.write("🔴 Bearish FVG:", [f"{round(fvg, 2)}" for fvg in fvgs['bearish'][:3]])

                        st.write("**Supply/Demand Zones:**")
                        if sd_zones.get('demand_zones'):
                            st.write("🟢 Demand:", [f"{round(dz, 2)}" for dz in sd_zones['demand_zones'][:3]])
                        if sd_zones.get('supply_zones'):
                            st.write("🔴 Supply:", [f"{round(sz, 2)}" for sz in sd_zones['supply_zones'][:3]])

                    # SMC Trading Rules Explanation
                    st.subheader("📚 SMC Trading Rules")
                    st.info("""
                    **🐂 Bullish Signals:**
                    - Price above Order Blocks + Fair Value Gaps
                    - Breaking above Liquidity Levels
                    - Entering Demand Zones
                    - Moving towards positive ICT SD extension levels

                    **🐻 Bearish Signals:**
                    - Price below Order Blocks + Fair Value Gaps
                    - Breaking below Liquidity Levels
                    - Entering Supply Zones
                    - Moving towards negative ICT SD extension levels

                    **⚡ Smart Money Concepts:**
                    - Order Blocks: Areas where large players placed orders
                    - Fair Value Gaps: Price inefficiencies to be filled
                    - Liquidity Levels: Areas with high trading activity
                    - ICT Standard Deviation (-2, -2.5, -4 Fibs): Mathematical projections of the algorithmic dealing range
                    """)

                except Exception as e:
                    st.error(f"❌ Error in SMC signal generation: {str(e)}")
                    st.info("This might be due to insufficient or invalid data for SMC analysis")

        except Exception as e:
            st.error(f"❌ Error in SMC analysis: {str(e)}")
            st.info("💡 SMC analysis requires sufficient price data with OHLC structure")
    col1, col2, col3 = st.columns(3)
    with col1:
        color = '🟢' if smc_signal['action'] == 'BUY' else '🔴' if smc_signal['action'] == 'SELL' else '🟡'
        st.metric(f"{color} SMC Signal", smc_signal['action'])
    with col2:
        st.metric("Confidence", f"{smc_signal['confidence']}%")
    with col3:
        st.info(smc_signal['reason'])
    
    st.divider()
    
    # Liquidity Levels
    st.subheader("💧 Liquidity Levels")
    liq_col1, liq_col2, liq_col3 = st.columns(3)
    with liq_col1:
        st.metric("Liquidity High", f"${liquidity['liquidity_high']:.2f}")
    with liq_col2:
        st.metric("Midpoint", f"${liquidity['midpoint']:.2f}")
    with liq_col3:
        st.metric("Liquidity Low", f"${liquidity['liquidity_low']:.2f}")
    
    st.divider()
    
    # Supply and Demand Zones
    st.subheader("📊 Supply & Demand Zones")
    sd_col1, sd_col2 = st.columns(2)
    
    with sd_col1:
        st.write("**📈 Demand Zones (Support)**")
        for i, zone in enumerate(sd_zones['demand_zones'], 1):
            st.write(f"  {i}. ${zone:.2f}")
    
    with sd_col2:
        st.write("**📉 Supply Zones (Resistance)**")
        for i, zone in enumerate(sd_zones['supply_zones'], 1):
            st.write(f"  {i}. ${zone:.2f}")
    
    st.divider()
    
    # Order Blocks
    st.subheader("🔲 Order Blocks")
    if order_blocks and any(order_blocks.values()):
        max_ob_len = max(len(v) for v in order_blocks.values())
        padded_ob = {k: v + [None]*(max_ob_len - len(v)) for k, v in order_blocks.items()}
        ob_data = pd.DataFrame(padded_ob)
        st.dataframe(ob_data, width='stretch')
    else:
        st.info("No significant order blocks detected recently")
    
    st.divider()
    
    # Fair Value Gaps
    st.subheader("⛳ Fair Value Gaps (FVG)")
    if fvgs and any(fvgs.values()):
        fvg_list = []
        for ftype, levels in fvgs.items():
            for level in levels:
                fvg_list.append({'type': ftype.capitalize(), 'level': level})
        if fvg_list:
            fvg_df = pd.DataFrame(fvg_list)
            st.dataframe(fvg_df[['type', 'level']], width='stretch')
        else:
            st.info("No recent fair value gaps detected")
        
        # Plot FVGs on chart
        fig_smc = go.Figure()
        
        # Add price data
        recent_data = data_for_smc.tail(100)
        fig_smc.add_trace(go.Scatter(
            x=recent_data.index,
            y=recent_data['Close'],
            mode='lines',
            name='Price',
            line=dict(color='blue', width=2)
        ))
        
        # Add liquidity levels
        fig_smc.add_hline(y=liquidity['liquidity_high'], line_dash="dash", line_color="green", 
                         annotation_text="Liquidity High", annotation_position="right")
        fig_smc.add_hline(y=liquidity['liquidity_low'], line_dash="dash", line_color="red", 
                         annotation_text="Liquidity Low", annotation_position="right")
        
        # Add supply and demand zones
        for zone in sd_zones['demand_zones']:
            fig_smc.add_hline(y=zone, line_dash="dot", line_color="lightgreen", 
                            annotation_text="Demand", annotation_position="left", opacity=0.5)
        
        for zone in sd_zones['supply_zones']:
            fig_smc.add_hline(y=zone, line_dash="dot", line_color="lightcoral", 
                            annotation_text="Supply", annotation_position="left", opacity=0.5)
        
        fig_smc.update_layout(
            title=f"{target_column} - SMC Analysis with Liquidity & Zones",
            xaxis_title="Date",
            yaxis_title="Price ($)",
            template="plotly_white",
            height=600
        )
        
        st.plotly_chart(fig_smc, width='stretch')
    else:
        st.info("No recent fair value gaps detected")

with tab5:
    st.header("📺 Indian TradingView Professional Charts")

    # Add a custom symbol search option
    search_col, _ = st.columns([1, 1])
    with search_col:
        tv_search = st.text_input("🔍 Search any Symbol", value="", help="e.g. AAPL, NSE:RELIANCE, BINANCE:BTCUSDT (Leave empty to use the selected asset)").strip()

    # Determine the symbol to display
    tv_target = tv_search.upper() if tv_search else target_column

    # Chart type selection
    chart_type = st.selectbox("Chart Type", ["Advanced Chart", "Mini Overview", "Symbol Info"])

    if chart_type == "Advanced Chart":
        st.subheader(f"📊 {tv_target} Advanced Indian TradingView Chart")
        st.info("🔗 Connected to https://in.tradingview.com/ for real-time professional charting")

        # Create TradingView embed
        symbol = tv_target if tv_target != 'BTC' else 'BTCUSD'
        tradingview_html = create_tradingview_embed(symbol)

        # Display the chart
        st.components.v1.html(tradingview_html, height=900)

        st.markdown("""
        **🇮🇳 Indian TradingView Features:**
        - 📈 Real-time price data from Indian markets
        - 🛠️ Professional trading tools
        - 📊 Multiple timeframes (1m, 5m, 15m, 1h, 1D, 1W, 1M)
        - 🎯 Technical indicators (MACD, RSI, Volume)
        - 📱 Mobile responsive design
        - 🌏 Indian timezone (Asia/Kolkata)
        """)

    elif chart_type == "Mini Overview":
        st.subheader(f"📈 {tv_target} Quick Overview")

        col1, col2 = st.columns(2)

        with col1:
            symbol = tv_target if tv_target != 'BTC' else 'BTCUSD'
            mini_chart = create_tradingview_mini_chart(symbol)
            st.components.v1.html(mini_chart, height=400)

        with col2:
            st.subheader("📊 Key Metrics")
            
            # Check if we have local data for the searched symbol, otherwise fallback to main target
            data_symbol = tv_target if tv_target in data.columns else target_column
            
            # For displaying current price safely
            display_price = current_prices.get(data_symbol)
            if display_price:
                st.metric("Current Price", f"${display_price:.2f}")

            # Show some technical indicators
            historical = data[data_symbol].dropna() if data_symbol in data.columns else pd.Series(dtype=float)
            if len(historical) > 0:
                change_24h = (historical.iloc[-1] - historical.iloc[-2]) if len(historical) > 1 else 0
                change_pct = (change_24h / historical.iloc[-2] * 100) if len(historical) > 1 else 0

                st.metric("24h Change", f"{change_24h:.2f}", f"{change_pct:.2f}%")

                # Simple volatility
                vol = historical.pct_change().std() * 100
                st.metric("Volatility", f"{vol:.2f}%")

    else:  # Symbol Info
        st.subheader(f"ℹ️ {tv_target} Symbol Information")

        # Get additional info from yfinance
        try:
            # Extract pure symbol if it contains exchange prefix
            yf_symbol = tv_target.split(':')[-1] if ':' in tv_target else tv_target
            
            if yf_symbol == 'BTC':
                ticker = yf.Ticker('BTC-USD')
            else:
                ticker = yf.Ticker(yf_symbol)

            info = ticker.info

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Market Cap", f"${info.get('marketCap', 'N/A'):,}" if info.get('marketCap') else "N/A")
                st.metric("Volume", f"{info.get('volume', 'N/A'):,}" if info.get('volume') else "N/A")

            with col2:
                st.metric("52W High", f"${info.get('fiftyTwoWeekHigh', 'N/A'):.2f}" if info.get('fiftyTwoWeekHigh') else "N/A")
                st.metric("52W Low", f"${info.get('fiftyTwoWeekLow', 'N/A'):.2f}" if info.get('fiftyTwoWeekLow') else "N/A")

            with col3:
                st.metric("PE Ratio", f"{info.get('trailingPE', 'N/A'):.2f}" if info.get('trailingPE') else "N/A")
                st.metric("Dividend Yield", f"{info.get('dividendYield', 'N/A'):.2f}%" if info.get('dividendYield') else "N/A")

            if info.get('longBusinessSummary'):
                st.subheader("Business Summary")
                st.write(info['longBusinessSummary'][:500] + "...")

        except Exception as e:
            st.error(f"Unable to fetch symbol information: {e}")

with tab6:
    st.header("📋 Model Performance")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("RMSE", f"${rmse:.2f}")
    with col2:
        st.metric("MAPE", f"{mape:.2f}%")
    st.subheader("Prediction vs Actual")
    comparison_fig = go.Figure()
    comparison_fig.add_trace(go.Scatter(
        x=list(range(len(val_predictions))),
        y=val_predictions,
        mode='lines',
        name='Predicted',
        line=dict(color='red', dash='dash')
    ))
    
    comparison_fig.update_layout(
        title="Validation Set: Predictions vs Actual",
        xaxis_title="Sample",
        yaxis_title="Price ($)",
        template="plotly_white"
    )
    
    st.plotly_chart(comparison_fig, width='stretch')

with tab7:
    st.header("🎯 Inner Circle Trader (ICT) Strategy")
    st.markdown("Advanced algorithmic trading framework capturing Optimal Trade Entry (OTE), AOX Sniper Fib Extensions, and standard deviation multipliers.")
    
    st.divider()
    st.subheader("Interactive Multi-Timeframe (MTF) Context")
    
    # Timeframe selection
    tf_options = ["1min", "3min", "5min", "15min", "30min", "1Hr", "4Hr", "1Day", "1W", "1M"]
    selected_tf_label = st.selectbox("Algorithmic Resolution", tf_options, index=5)
    
    # Internal map — NOTE: 1Hr & 4Hr use 30m base + resample workaround
    # because Yahoo Finance's native '1h' interval is currently unavailable.
    tf_map = {
        "1min": "1m", "3min": "1m", "5min": "5m",
        "15min": "15m", "30min": "30m", "1Hr": "30m",
        "4Hr": "30m", "1Day": "1d", "1W": "1wk", "1M": "1mo"
    }
    
    with st.spinner(f"Extracting highly granular {selected_tf_label} market data..."):
        try:
            # Map symbol using the central yahoo_mapping dict (covers all asset types)
            yf_symbol = yahoo_mapping.get(target_column, target_column)
                
            yf_period = "1y"
            yf_interval = tf_map[selected_tf_label]  # always a valid Yahoo Finance interval

            # --- AUTO-REFRESH LIVE DATA ---
            refresh_tv_cache(target_column, yf_interval)

            # --- TRADINGVIEW CACHE LOADING ---
            cache_file = f"tv_live_cache/{target_column}_{yf_interval}.csv"
            chart_hist = pd.DataFrame()
            
            if os.path.exists(cache_file):
                try:
                    chart_hist = pd.read_csv(cache_file, index_col=0, parse_dates=True)
                    # Convert TV columns (lower) to YF format (Title) if needed
                    if 'close' in chart_hist.columns:
                        chart_hist = chart_hist.rename(columns={
                            'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'
                        })
                    st.sidebar.success(f"✅ Using Live TradingView Data ({selected_tf_label})")
                except Exception as e:
                    st.sidebar.warning(f"⚠ Cache read error: {e}")

            if chart_hist.empty:
                # Only use yfinance fallback for US Stocks
                if selected_category == "🇺🇸 US Stocks":
                    if selected_tf_label in ["1min", "3min", "5min"]:
                        yf_period = "5d"
                    elif selected_tf_label in ["15min", "30min", "1Hr", "4Hr"]:
                        import datetime as _dt
                        _end   = _dt.datetime.now()
                        _start = _end - _dt.timedelta(days=58)
                        chart_hist = yf.Ticker(yf_symbol).history(
                            start=_start.strftime("%Y-%m-%d"),
                            end=_end.strftime("%Y-%m-%d"),
                            interval=yf_interval
                        )
                    else:
                        chart_hist = yf.Ticker(yf_symbol).history(period=yf_period, interval=yf_interval)
                else:
                    st.error(f"⚠️ TradingView data is not available for {target_column} at {selected_tf_label} resolution. Please refresh.")
                    st.stop()

            if chart_hist.empty:
                st.error(f"⚠️ Yahoo Finance returned no data for {selected_tf_label}. Try a different timeframe.")
            else:
                # Proper UTC-4 Timezone alignment natively
                if chart_hist.index.tz is None:
                    chart_hist.index = chart_hist.index.tz_localize('UTC').tz_convert('America/New_York')
                else:
                    chart_hist.index = chart_hist.index.tz_convert('America/New_York')
                    
                # Resample from 30m base where Yahoo Finance's native '1h' is unavailable
                if selected_tf_label == "3min":
                    chart_hist = chart_hist.resample('3min').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'}).dropna()
                elif selected_tf_label == "1Hr":
                    chart_hist = chart_hist.resample('1h').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'}).dropna()
                elif selected_tf_label == "4Hr":
                    chart_hist = chart_hist.resample('4h').agg({'Open':'first', 'High':'max', 'Low':'min', 'Close':'last', 'Volume':'sum'}).dropna()
                    
                # Prepare dealing logic safely grabbing last 100 periods
                df_for_ict = chart_hist.tail(100).copy()
                
                ote_levels = ICTStrategy.find_ote_fib_levels(df_for_ict)
                aox_levels = ICTStrategy.find_aox_fib_levels(df_for_ict)
                stdev_levels = ICTStrategy.find_standard_deviation_levels(df_for_ict)
                
                # DRAW LIVE MTF CHART
                fig_mtf = go.Figure(data=[go.Candlestick(
                    x=df_for_ict.index,
                    open=df_for_ict['Open'],
                    high=df_for_ict['High'],
                    low=df_for_ict['Low'],
                    close=df_for_ict['Close'],
                    name="Candlesticks"
                )])
                
                # Explicit proper values fixing truncating decimals
                tick_format = ".5f" if df_for_ict['Close'].mean() < 10 else ".2f"
                
                fig_mtf.update_layout(
                    title=f"【{yf_symbol}】 {selected_tf_label} Algorithmic MTF View (UTC-4 New York)",
                    xaxis_title="NY Local Time",
                    yaxis_title="Price Tracking ($)",
                    yaxis_tickformat=tick_format, # Forces strict decimals matching asset scale
                    template="plotly_dark",
                    height=700,
                    xaxis_rangeslider_visible=False,
                    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
                )
                
                # Apply plotting properties if logic successfully fired
                if ote_levels:
                    # Plot boundaries
                    fig_mtf.add_hline(y=ote_levels['swing_high'], line_dash="dash", line_color="lime", annotation_text="Swing High")
                    fig_mtf.add_hline(y=ote_levels['swing_low'], line_dash="dash", line_color="orange", annotation_text="Swing Low")
                    
                    # Add OTE logic visual
                    for lbl, val in ote_levels.get('levels', {}).items():
                        if "70.5" in lbl:
                            fig_mtf.add_hline(y=val, line_dash="dot", line_color="gold", annotation_text=lbl)

                st.plotly_chart(fig_mtf, use_container_width=True)

                # RENDER TEXTUAL BOUNDS
                if ote_levels:
                    direction_emoji = "🐻 Downward Institutional Sweep" if ote_levels.get('direction') == 'bearish' else "🐂 Upward Institutional Sweep"
                    st.subheader(f"🔄 Active {selected_tf_label} Dealing Range ({direction_emoji})")
                    
                    range_col1, range_col2 = st.columns(2)
                    with range_col1:
                        st.metric("Swing High", f"${ote_levels['swing_high']:.5f}")
                    with range_col2:
                        st.metric("Swing Low", f"${ote_levels['swing_low']:.5f}")
                        
                    st.divider()
                    
                    # Rendering Layout columns
                    ict_col1, ict_col2, ict_col3 = st.columns(3)
                    
                    with ict_col1:
                        st.write("**🏹 OTE Fib Retracement**")
                        st.info("Optimal entry coordinates.")
                        for lbl, price in ote_levels.get('levels', {}).items():
                            if "70.5" in lbl:
                                st.write(f"🌟 **{lbl}: ${price:.5f}**")
                            else:
                                st.write(f"• {lbl}: ${price:.5f}")
                                
                    with ict_col2:
                        st.write("**🎯 AOX Sniper Extensions**")
                        st.info("Structural algorithmic multipliers.")
                        for lbl, price in list(aox_levels.get('levels', {}).items()):
                            if "Target" in lbl:
                                st.write(f"💥 **{lbl}**: ${price:.5f}")
                            elif "Inner" in lbl:
                                st.write(f"➖ {lbl}: ${price:.5f}")
                                
                    with ict_col3:
                        st.write("**📏 Standard Deviation Projections**")
                        st.info("Algorithmic structural shifts.")
                        for lvl, price in stdev_levels.get('levels', {}).items():
                            st.write(f"• {lvl} SD: ${price:.5f}")

                else:
                    st.info("Not enough valid swings logged in this timeframe view.")
                    
        except Exception as e:
            st.error(f"Error compiling MTF chart environment: {str(e)}")

        st.divider()
        
        with st.expander("🕛 Midnight Killzone Strategy (1-Minute Short Term)"):
            st.markdown("Identifies the London/New York midnight crossover algorithmic sweep. Retrieves highly specific 1-min standard deviations and 1st FVG validation metrics natively via live data fetching.")
            
            with st.spinner("Fetching Live 1-Minute Algorithm Data..."):
                # Ensure 1m cache is fresh for the midnight logic
                refresh_tv_cache(target_column, '1m')
                
                # Pass target_column directly to ensure cache file names match
                midnight_data = ICTStrategy.calculate_midnight_setup(target_column)
                
            if "error" in midnight_data:
                st.error(midnight_data["error"])
            else:
                st.success(f"Successfully processed midnight dealing range for **{midnight_data['date']}**")
                
                m_col1, m_col2, m_col3 = st.columns(3)
                with m_col1:
                    st.metric("Killzone High (12:01-12:29 AM)", f"${midnight_data['high']:.2f}")
                with m_col2:
                    st.metric("Killzone Low (12:01-12:29 AM)", f"${midnight_data['low']:.2f}")
                with m_col3:
                    st.metric("Dealing Range Size", f"${midnight_data['range']:.2f}")
                    
                st.write("**First Fair Value Gap (FVG) Trigger**")
                if midnight_data['fvg_price'] is not None:
                    fvg_icon = "🟢" if midnight_data['fvg_type'] == "Bullish" else "🔴"
                    st.info(f"{fvg_icon} Identified {midnight_data['fvg_type']} FVG at **${midnight_data['fvg_price']:.2f}** (Time: {midnight_data['fvg_time']} EST)")
                else:
                    st.warning("No structural FVG found inside the 29-minute killzone window.")
                    
                st.divider()
                st.write("**Bidirectional Liquidity Targets (Standard Deviations)**")
                sd_col1, sd_col2 = st.columns(2)
                
                with sd_col1:
                    st.write("**📈 Buy-Side Targets (Upside)**")
                    for lbl, tgt in midnight_data['buy_targets'].items():
                        st.write(f"• {lbl}: **${tgt:.2f}**")
                        
                with sd_col2:
                    st.write("**📉 Sell-Side Targets (Downside)**")
                    for lbl, tgt in midnight_data['sell_targets'].items():
                        st.write(f"• {lbl}: **${tgt:.2f}**")
                        
                if midnight_data.get('full_day_data'):
                    try:
                        import json
                        chart_df = pd.read_json(io.StringIO(midnight_data['full_day_data'])) if hasattr(pd, 'read_json') else pd.read_json(midnight_data['full_day_data'])
                        fig_ny = go.Figure(data=[go.Candlestick(
                            x=chart_df.index,
                            open=chart_df['Open'],
                            high=chart_df['High'],
                            low=chart_df['Low'],
                            close=chart_df['Close']
                        )])
                        
                        # Add Killzone ranges
                        fig_ny.add_hline(y=midnight_data['high'], line_dash="dash", line_color="lime", annotation_text="Killzone High")
                        fig_ny.add_hline(y=midnight_data['low'], line_dash="dash", line_color="orange", annotation_text="Killzone Low")
                        
                        # Sub-plot buy/sell SDs implicitly as reference lines
                        for lbl, val in midnight_data['buy_targets'].items():
                            if "1 SD" in lbl or "2 SD" in lbl or "4 SD" in lbl:
                                fig_ny.add_hline(y=val, line_dash="dot", line_color="green", annotation_text=lbl, opacity=0.4)
                                
                        for lbl, val in midnight_data['sell_targets'].items():
                            if "1 SD" in lbl or "2 SD" in lbl or "4 SD" in lbl:
                                fig_ny.add_hline(y=val, line_dash="dot", line_color="red", annotation_text=lbl, opacity=0.4)
                        
                        fig_ny.update_layout(
                            title=f"{target_column} - 1m Local NY Format (UTC-4) - {midnight_data.get('killzone_name', 'Midnight/NY Open')}",
                            xaxis_title="Time (UTC-4)",
                            yaxis_title="Price ($)",
                            template="plotly_dark",
                            height=600,
                            xaxis_rangeslider_visible=False
                        )
                        st.plotly_chart(fig_ny, use_container_width=True)
                    except Exception as e:
                        st.error(f"Could not render 1m interactive chart: {str(e)}")
