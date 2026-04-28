@echo off
echo 🚀 Starting TradingView Data Collection Service
echo 📊 Collecting data from TradingView and Yahoo Finance
echo 🔄 Continuous updates every 60 minutes
echo Press Ctrl+C to stop
echo.

cd /d "%~dp0"
python tradingview_data_collector.py --continuous --interval 60

echo.
echo 🛑 Data collection service stopped
pause