import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

def create_tradingview_chart(data, target_column, height=500):
    """
    Create an interactive TradingView-style chart using lightweight-charts
    """
    from streamlit_lightweight_charts import LightweightCharts
    
    # Prepare OHLCV data
    chart_data = []
    for idx, row in data.tail(500).iterrows():
        timestamp = int(idx.timestamp()) if hasattr(idx, 'timestamp') else 0
        chart_data.append({
            "time": timestamp,
            "open": float(row[target_column] * 0.98),  # Simulated OHLC
            "high": float(row[target_column] * 1.02),
            "low": float(row[target_column] * 0.97),
            "close": float(row[target_column]),
            "volume": float(np.random.randint(1000000, 5000000))
        })
    
    chart_colors = {
        "background": "#1a1a1a",
        "textColor": "#CCCCCF"
    }
    
    try:
        chart = LightweightCharts()
        chart.set(chart_colors)
        
        # Add candlestick series
        chart.candlestick(chart_data)
        
        # Add volume bar chart
        volume_data = [{"time": d["time"], "value": d["volume"], "color": "#26a69a" if d["close"] > d["open"] else "#ef5350"} 
                       for d in chart_data]
        chart.volume(volume_data)
        
        return chart
    except Exception as e:
        return None

def create_tradingview_embed(symbol):
    """
    Create embedded TradingView widget for live trading using Indian TradingView
    Supports stocks, forex, metals, commodities, and crypto
    """
    # Comprehensive exchange mapping for all asset types
    exchange_map = {
        # US Stocks
        'AMZN': 'NASDAQ', 'DPZ': 'NASDAQ', 'NFLX': 'NASDAQ', 'AAPL': 'NASDAQ',
        'GOOGL': 'NASDAQ', 'MSFT': 'NASDAQ', 'TSLA': 'NASDAQ', 'NVDA': 'NASDAQ',

        # Indian Stocks
        'RELIANCE': 'NSE', 'TCS': 'NSE', 'HDFCBANK': 'NSE', 'ICICIBANK': 'NSE',
        'INFY': 'NSE', 'BAJFINANCE': 'NSE', 'HINDUNILVR': 'NSE', 'ITC': 'NSE',
        'KOTAKBANK': 'NSE', 'LT': 'NSE',

        # Forex
        'EURUSD': 'FX', 'GBPUSD': 'FX', 'USDJPY': 'FX', 'USDCHF': 'FX',
        'AUDUSD': 'FX', 'USDCAD': 'FX', 'NZDUSD': 'FX', 'EURJPY': 'FX', 'GBPJPY': 'FX',

        # Metals & Commodities
        'GOLD': 'COMEX', 'SILVER': 'COMEX', 'COPPER': 'COMEX', 'PLATINUM': 'COMEX',
        'XAUUSD': 'FX', 'XAGUSD': 'FX', 'XCUUSD': 'FX', 'XPTUSD': 'FX',
        'WTI_CRUDE': 'NYMEX', 'BRENT_CRUDE': 'ICE',

        # Crypto
        'BTC': 'CRYPTO', 'ETH': 'CRYPTO', 'BNB': 'CRYPTO', 'ADA': 'CRYPTO', 'SOL': 'CRYPTO'
    }

    if ':' in symbol:
        symbol_code = symbol
        exchange = symbol.split(':')[0]
    else:
        exchange = exchange_map.get(symbol, 'NASDAQ')

        # Format symbol for TradingView
        if exchange == 'FX':
            symbol_code = f"{symbol}"
        elif exchange == 'CRYPTO':
            symbol_code = f"{exchange}:{symbol}USD" if symbol != 'BTC' else f"{exchange}:{symbol}USD"
        elif exchange in ['COMEX', 'NYMEX', 'ICE']:
            symbol_code = f"{exchange}:{symbol}"
        else:
            symbol_code = f"{exchange}:{symbol}"

    # Adjust timezone and locale based on asset type
    if exchange == 'NSE':
        timezone = "Asia/Kolkata"
        locale = "in"
    elif exchange == 'FX':
        timezone = "UTC"
        locale = "en"
    else:
        timezone = "America/New_York"
        locale = "en"

    tradingview_html = f"""
    <div class="tradingview-widget-container" style="width: 100%; height: 100%;">
        <div id="tradingview-chart" style="width: 100%; height: 100vh;"></div>
        <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
        <script type="text/javascript">
            new TradingView.widget(
            {{
            "autosize": true,
            "symbol": "{symbol_code}",
            "interval": "D",
            "timezone": "{timezone}",
            "theme": "dark",
            "style": "1",
            "locale": "{locale}",
            "toolbar_bg": "#f1f3f6",
            "enable_publishing": false,
            "allow_symbol_change": true,
            "container_id": "tradingview-chart",
            "studies": [
                "Volume@tv-basicstudies",
                "MACD@tv-basicstudies",
                "RSI@tv-basicstudies"
            ],
            "show_popup_button": true,
            "popup_width": "1000",
            "popup_height": "650"
            }}
            )
        </script>
    </div>
    """
    return tradingview_html

def create_tradingview_mini_chart(symbol):
    """
    Create mini TradingView chart for quick overview using Indian TradingView
    Supports all asset types: stocks, forex, metals, commodities, crypto
    """
    # Comprehensive exchange mapping
    exchange_map = {
        # US Stocks
        'AMZN': 'NASDAQ', 'DPZ': 'NASDAQ', 'NFLX': 'NASDAQ', 'AAPL': 'NASDAQ',
        'GOOGL': 'NASDAQ', 'MSFT': 'NASDAQ', 'TSLA': 'NASDAQ', 'NVDA': 'NASDAQ',

        # Indian Stocks
        'RELIANCE': 'NSE', 'TCS': 'NSE', 'HDFCBANK': 'NSE', 'ICICIBANK': 'NSE',
        'INFY': 'NSE', 'BAJFINANCE': 'NSE', 'HINDUNILVR': 'NSE', 'ITC': 'NSE',
        'KOTAKBANK': 'NSE', 'LT': 'NSE',

        # Forex
        'EURUSD': 'FX', 'GBPUSD': 'FX', 'USDJPY': 'FX', 'USDCHF': 'FX',
        'AUDUSD': 'FX', 'USDCAD': 'FX', 'NZDUSD': 'FX', 'EURJPY': 'FX', 'GBPJPY': 'FX',

        # Metals & Commodities
        'GOLD': 'COMEX', 'SILVER': 'COMEX', 'COPPER': 'COMEX', 'PLATINUM': 'COMEX',
        'XAUUSD': 'FX', 'XAGUSD': 'FX', 'XCUUSD': 'FX', 'XPTUSD': 'FX',
        'WTI_CRUDE': 'NYMEX', 'BRENT_CRUDE': 'ICE',

        # Crypto
        'BTC': 'CRYPTO', 'ETH': 'CRYPTO', 'BNB': 'CRYPTO', 'ADA': 'CRYPTO', 'SOL': 'CRYPTO'
    }

    if ':' in symbol:
        tv_exchange, display_symbol = symbol.split(':', 1)
        exchange = tv_exchange
    else:
        exchange = exchange_map.get(symbol, 'NASDAQ')

        # Format symbol for TradingView mini chart
        if exchange == 'FX':
            display_symbol = symbol
            tv_exchange = "FX_IDC"
        elif exchange == 'CRYPTO':
            display_symbol = f"{symbol}USD" if symbol != 'BTC' else "BTCUSD"
            tv_exchange = "CRYPTO"
        elif exchange in ['COMEX', 'NYMEX', 'ICE']:
            display_symbol = symbol
            tv_exchange = exchange
        else:
            display_symbol = symbol
            tv_exchange = exchange

    # Adjust locale based on asset type
    locale = "in" if exchange == 'NSE' else "en"

    tradingview_mini = f"""
    <div class="tradingview-widget-container" style="width: 100%; height: 100%;">
        <div class="tradingview-widget-container__widget" style="width: 100%; height: 400px;"></div>
        <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-mini-symbol-overview.js" async>
        {{
        "symbols": [
            [
                "{display_symbol}",
                "{tv_exchange}"
            ]
        ],
        "chartOnly": false,
        "width": "100%",
        "height": "100%",
        "locale": "{locale}",
        "colorTheme": "dark",
        "autosize": true,
        "showVolume": true,
        "showMA": true,
        "hideDateRanges": false,
        "hideMarketStatus": false,
        "hideSymbolLogo": false,
        "scalePosition": "right",
        "scaleMode": "Normal",
        "fontFamily": "-apple-system, BlinkMacSystemFont, 'Trebuchet MS', Roboto, Ubuntu, sans-serif",
        "fontSize": "10",
        "noTimeScale": false,
        "valuesTracking": "1",
        "changeMode": "price-and-percent",
        "chartType": "area",
        "lineWidth": 2,
        "lineType": 0,
        "dateRanges": [
            "1d|1",
            "1m|30",
            "3m|60",
            "12m|1D",
            "60m|1W",
            "all|1M"
        ]
        }}
        </script>
    </div>
    """
    return tradingview_mini
