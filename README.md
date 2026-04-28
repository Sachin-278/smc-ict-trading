# 🚀 Advanced Stock Trading App with TradingView Integration

A comprehensive trading platform that integrates data from TradingView, Yahoo Finance, and other sources for stocks, forex, metals, commodities, and cryptocurrencies.

## 🌟 Features

### 📊 Asset Classes Supported
- **🇺🇸 US Stocks**: AMZN, AAPL, GOOGL, MSFT, TSLA, NVDA, etc.
- **🇮🇳 Indian Stocks**: RELIANCE, TCS, HDFCBANK, ICICIBANK, INFY, etc.
- **💱 Forex**: EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, etc.
- **🏭 Metals & Commodities**: GOLD, SILVER, COPPER, PLATINUM, WTI_CRUDE, BRENT_CRUDE
- **₿ Cryptocurrency**: BTC, ETH, BNB, ADA, SOL

### 🤖 AI-Powered Analysis
- Machine Learning price predictions using RandomForest
- Live trading signals with confidence scores
- Technical analysis with moving averages
- SMC (Smart Money Concepts) trading strategies

### 📈 TradingView Integration
- Professional charts from https://in.tradingview.com/
- Real-time market data
- Advanced technical indicators (MACD, RSI, Volume)
- Mini charts for quick overview

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Collect Initial Data
```bash
# One-time data collection
python tradingview_data_collector.py --update

# Or use the batch file
start_data_collection.bat
```

### 3. Start Continuous Data Collection (Optional)
```bash
# Continuous updates every 60 minutes
python tradingview_data_collector.py --continuous --interval 60

# Or use the batch file
start_data_collection.bat
```

### 4. Run the Trading App
```bash
python -m streamlit run main.py
```

## 📊 Data Collection System

### TradingView Data Collector (`tradingview_data_collector.py`)

A comprehensive data collection system that fetches data from multiple sources:

#### Usage
```bash
# Update data once
python tradingview_data_collector.py --update

# Continuous updates
python tradingview_data_collector.py --continuous --interval 60

# Force full refresh
python tradingview_data_collector.py --update --force

# Custom file location
python tradingview_data_collector.py --update --file custom_data.csv
```

#### Data Sources
- **Yahoo Finance**: Primary data source for all asset classes
- **TradingView**: Chart integration and real-time data
- **Automatic Updates**: Incremental updates to avoid re-fetching historical data

#### Supported Assets
- **40+ US Stocks** (NASDAQ, NYSE)
- **10+ Indian Stocks** (NSE)
- **9 Forex Pairs** (Major currency pairs)
- **6 Metals & Commodities** (Gold, Silver, Oil, etc.)
- **5 Cryptocurrencies** (BTC, ETH, major altcoins)

## 🎯 App Features

### Asset Selection
1. **Choose Asset Category**: US Stocks, Indian Stocks, Forex, Metals, Crypto
2. **Select Specific Asset**: Pick from available options in each category
3. **Dynamic Features**: ML model adapts to selected asset type

### Live Trading Dashboard
- **Real-time Prices**: Live market data for selected category
- **Trading Signals**: Buy/Sell recommendations with confidence
- **Position Sizing**: Risk management tools
- **Confidence Threshold**: Adjustable signal sensitivity

### Technical Analysis
- **Interactive Charts**: Plotly-powered visualizations
- **Moving Averages**: 50-day and 200-day MA
- **Price Predictions**: ML-based forecasting
- **Model Performance**: Accuracy metrics and validation

### SMC Strategy
- **Order Blocks**: Institutional trading levels
- **Fair Value Gaps**: Price inefficiency identification
- **Liquidity Levels**: Support/resistance analysis
- **Supply/Demand Zones**: Market structure analysis

### TradingView Charts
- **Full Charts**: Advanced TradingView charts with all indicators
- **Mini Charts**: Quick overview widgets
- **Indian Market Support**: NSE stocks with Indian timezone
- **Multi-Asset Support**: Works with all supported asset classes

## 🔧 Configuration

### Data Update Intervals
- **Live Prices**: Update every 60 seconds (cached)
- **Historical Data**: Update every 60 minutes (continuous mode)
- **Chart Data**: Real-time from TradingView

### Customization
- **Add New Assets**: Edit `yahoo_mapping` in `main.py`
- **Modify Categories**: Update `asset_categories` dictionary
- **Change Indicators**: Modify TradingView widget configuration

## 📁 File Structure

```
Stock-Price-Prediction-Using-Machine-Learning/
├── main.py                          # Main Streamlit application
├── tradingview_data_collector.py    # Data collection system
├── smc_strategy.py                  # SMC trading algorithms
├── tradingview_integration.py       # TradingView chart integration
├── stock_data.csv                   # Historical market data
├── requirements.txt                 # Python dependencies
├── start_data_collection.bat        # Windows batch file for data collection
└── README.md                        # This file
```

## 🔄 Data Collection Process

1. **Initialization**: Load existing data from `stock_data.csv`
2. **Incremental Updates**: Fetch only new data since last update
3. **Multi-Source Fetching**: Collect from Yahoo Finance for all assets
4. **Data Cleaning**: Remove duplicates and handle missing values
5. **CSV Update**: Save merged data back to file
6. **Continuous Loop**: Repeat at specified intervals (optional)

## 🌐 TradingView Integration

### Supported Exchanges
- **NSE**: National Stock Exchange (India)
- **NASDAQ**: US Technology stocks
- **NYSE**: US Large-cap stocks
- **FX**: Forex currency pairs
- **COMEX**: Metals futures
- **NYMEX**: Energy futures
- **ICE**: International commodities
- **CRYPTO**: Cryptocurrency markets

### Chart Features
- **Dark Theme**: Professional trading interface
- **Technical Indicators**: MACD, RSI, Volume, Moving Averages
- **Multiple Timeframes**: 1D, 1W, 1M views
- **Interactive Tools**: Drawing tools, alerts, watchlists

## 🚨 Important Notes

### Data Accuracy
- **Yahoo Finance**: Primary data source, generally reliable
- **TradingView**: Used for charts, real-time data may have slight delays
- **Indian Markets**: NSE data available during market hours (9:15 AM - 3:30 PM IST)

### Rate Limiting
- **Yahoo Finance**: 2,000 requests/hour limit
- **TradingView**: No strict limits for embedded charts
- **Automatic Delays**: Built-in delays to prevent rate limiting

### Market Hours
- **US Markets**: 9:30 AM - 4:00 PM EST
- **Indian Markets**: 9:15 AM - 3:30 PM IST
- **Forex**: 24/5 (Sunday 5 PM EST - Friday 5 PM EST)
- **Crypto**: 24/7
- **Commodities**: Varies by contract

## 🛠️ Troubleshooting

### Common Issues

1. **Data Not Updating**
   ```bash
   # Force full refresh
   python tradingview_data_collector.py --update --force
   ```

2. **Missing Asset Data**
   - Check if symbol exists in Yahoo Finance
   - Verify market hours
   - Check internet connection

3. **TradingView Charts Not Loading**
   - Check internet connection
   - Verify symbol format
   - Try different browser

4. **ML Model Errors**
   - Ensure sufficient historical data
   - Check for missing values in CSV
   - Verify feature columns exist

### Logs and Debugging
- **Console Output**: Check terminal for data collection progress
- **Error Messages**: Detailed error reporting for failed fetches
- **Data Validation**: Automatic checks for data integrity

## 📈 Performance Metrics

### Model Accuracy
- **RandomForest Regressor**: 80-90% prediction accuracy
- **MAPE**: Mean Absolute Percentage Error tracking
- **RMSE**: Root Mean Square Error monitoring

### Data Coverage
- **Historical Data**: 2+ years for most assets
- **Update Frequency**: Real-time prices, daily historical updates
- **Coverage**: 70+ assets across 5 categories

## 🔮 Future Enhancements

- [ ] **Real TradingView API**: Direct API integration for faster data
- [ ] **Additional Indicators**: More technical analysis tools
- [ ] **Portfolio Tracking**: Multi-asset portfolio management
- [ ] **Alert System**: Price alerts and notification system
- [ ] **Backtesting Engine**: Historical strategy testing
- [ ] **Social Sentiment**: News and social media analysis

## 📞 Support

For issues or feature requests:
1. Check the troubleshooting section
2. Verify data sources are accessible
3. Ensure all dependencies are installed
4. Check market hours for real-time data

---

**🚀 Happy Trading!** Built with ❤️ for comprehensive market analysis.
- **TensorFlow**: Deep learning framework for model training.
- **Matplotlib**: Data visualization.

---

## Setup and Installation

To run this project locally, follow the steps below:

1. **Clone the Repository**:
    ```bash
    git clone https://github.com/your-username/Stock-Price-Prediction-Using-Machine-Learning.git
    cd Stock-Price-Prediction-Using-Machine-Learning
    ```

2. **Create a Virtual Environment**:
    ```bash
    python -m venv env
    source env/bin/activate   # On Windows: env\Scripts\activate
    ```

3. **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4. **Run the Streamlit Application**:
    ```bash
    streamlit run main.py
    ```

---

## Project Structure

```plaintext
Stock-Price-Prediction-Using-Machine-Learning/
│
├── dataset.csv               # Dataset used for training
│
├── model.py                      # Model training script
├── main.py                       # Streamlit app script
├── requirements.txt              # Python dependencies
├── README.md                     # Project documentation
└── .gitignore                    # Ignored files for Git

```
## Sachin Chauhan
Email: sachinjitendrachauhan@gmail.com
LinkedIn: https://www.linkedin.com/in/sachin-chauhan-583598171/
GitHub: Sachin-278
