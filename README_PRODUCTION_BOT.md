# 🤖 Production-Grade MT5 Trading Bot

A professional, industrial-strength trading bot that collects data from MetaTrader 5 and performs Smart Money Concepts (SMC) analysis with real-time progress tracking.

## ✨ Features

- ✅ **Real-time Progress Tracking** - See exactly what's happening on the console
- ✅ **Timeout Protection** - Never hangs - operations have timeouts
- ✅ **Automatic Retry** - Intelligent retry logic for failed operations
- ✅ **Data Caching** - Fast repeated runs with intelligent caching
- ✅ **Error Recovery** - Graceful error handling and recovery
- ✅ **Professional Logging** - Detailed logs for debugging
- ✅ **Production-Ready** - Battle-tested code with best practices
- ✅ **Multi-Symbol Support** - Analyze multiple symbols simultaneously
- ✅ **Multi-Timeframe Analysis** - D1, H4, H1 analysis
- ✅ **CSV Reports** - Professional reports with timestamp

## 🚀 Quick Start

### Windows

```batch
# Easy way - double click:
start_production_bot.bat

# Or from command line:
start_production_bot.bat GBPUSD,XAUUSD,EURUSD
```

### Linux/Mac

```bash
# Make executable (first time only)
chmod +x start_production_bot.sh

# Run with default symbols
./start_production_bot.sh

# Run with custom symbols
./start_production_bot.sh GBPUSD,EURUSD,USDJPY
```

### Direct Python

```bash
# Install dependencies first
pip install pandas numpy yfinance

# Run the bot
python3 run_bot.py GBPUSD,XAUUSD,EURUSD
```

## 📋 Requirements

- **Python 3.8+** (required)
- **pandas** - Data manipulation
- **numpy** - Numerical operations
- **MetaTrader5** - MT5 connection (Windows only, optional)
- **yfinance** - Fallback data source (optional)

## 🎯 What You'll See

When you run the bot, you'll see real-time progress like this:

```
══════════════════════════════════════════════════════════════════════
                  🤖 PRODUCTION MT5 TRADING BOT                     
══════════════════════════════════════════════════════════════════════

[1/5] Initializing components...
  ⏳ Loading DataManager...
  ✅ DataManager loaded
  ⏳ Loading SMC Analyzer...
  ✅ SMC Analyzer loaded

[2/5] Connecting to MetaTrader 5...
  ⏳ Establishing connection...
     Server: ExnessKE-MT5Trial9
     Account: 211744072
  ✅ Connected to MT5 successfully!

[3/5] Collecting market data from MT5...

  Time     | Status Symbol     | TF    | Bars  | Progress
  ----------------------------------------------------------------------
  20:00:15 | ✅ GBPUSD     | D1    |   120 bars                [1/9]
  20:00:16 | ✅ GBPUSD     | H4    |   540 bars                [2/9]
  20:00:17 | ✅ GBPUSD     | H1    |  2160 bars                [3/9]
  20:00:18 | ✅ XAUUSD     | D1    |   120 bars                [4/9]
  ...

  ✅ Data collection complete: 3/3 symbols
  📊 Total timeframes collected: 9

[4/5] Analyzing market structure (SMC)...

  Analyzing 3 symbols...
  Symbol     | Bias     | Confidence   | Progress
  ------------------------------------------------------------
  🟢 GBPUSD     | 📈 BULLISH  |   82.5% confidence              [1/3] (2.1s)
  🟡 XAUUSD     | ➡️ NEUTRAL  |   45.0% confidence              [2/3] (1.8s)
  🟢 EURUSD     | 📉 BEARISH  |   78.0% confidence              [3/3] (2.0s)

  ✅ Analysis complete: 3/3 symbols

[5/5] Generating report...
  ✅ CSV report saved: bot_results_20251020_200025.csv

  📊 Summary:
     Total analyzed: 3
     📈 Bullish: 1
     📉 Bearish: 1
     ➡️ Neutral: 1
     🟢 High confidence (75%+): 2

══════════════════════════════════════════════════════════════════════
                   ✅ BOT COMPLETED SUCCESSFULLY                     
══════════════════════════════════════════════════════════════════════
  ⏱️ Total time: 12.5 seconds
  📊 Symbols processed: 3
  ✅ Success!
```

## 📊 Output Files

The bot generates the following files:

- **`bot_results_YYYYMMDD_HHMMSS.csv`** - Analysis results with timestamp
- **`data/SYMBOL_TIMEFRAME.csv`** - Cached data files
- **`logs/bot_run_YYYYMMDD_HHMMSS.log`** - Detailed execution logs

## 🔧 Configuration

### Environment Variables

You can customize the bot behavior using environment variables:

```bash
# MT5 Connection
export MT5_LOGIN=12345678
export MT5_PASSWORD=your_password
export MT5_SERVER=YourBroker-Server
export MT5_PATH=/path/to/terminal64.exe

# Timeouts
export MT5_TIMEOUT_MS=30000       # 30 seconds
export MT5_MAX_RETRIES=3          # Retry attempts
export MT5_RETRY_DELAY=2.0        # Seconds between retries
```

### Command Line Options

```bash
# Analyze specific symbols
python3 run_bot.py GBPUSD,EURUSD,USDJPY

# Single symbol
python3 run_bot.py XAUUSD

# Multiple symbols
python3 run_bot.py "GBPUSD,EURUSD,USDJPY,AUDUSD"
```

## 🐛 Troubleshooting

### Bot Hangs at "Analyzing Data"

**Fixed!** This version includes:
- ✅ Timeout protection (30s per operation)
- ✅ Real-time progress tracking
- ✅ Automatic retry logic
- ✅ Better error messages

### "No Module Named pandas"

```bash
pip install pandas numpy
```

### MT5 Connection Issues

1. **Check MT5 is running** on Windows
2. **Verify credentials** in environment variables
3. **Check logs** in `logs/` directory
4. **Try demo account** for testing

### No Data Collected

1. **Check symbol names** - use exact broker symbols
2. **Check internet connection**
3. **Verify MT5 terminal** is logged in
4. **Check logs** for specific errors

## 🔒 Security Notes

**IMPORTANT**: The default credentials in the code are for DEMO accounts only.

For production:
1. **Use environment variables** for credentials
2. **Never commit** credentials to git
3. **Use secure password** storage
4. **Enable 2FA** on your broker account

```bash
# Set environment variables (Linux/Mac)
export MT5_LOGIN=your_account
export MT5_PASSWORD=your_password
export MT5_SERVER=your_server

# Then run
python3 run_bot.py
```

## 📁 Project Structure

```
.
├── run_bot.py                    # Main bot entry point
├── data_manager.py               # MT5 data collection
├── smc_analyzer_production.py    # SMC analysis engine
├── mt5_connector.py              # MT5 connection manager
├── start_production_bot.sh       # Linux/Mac launcher
├── start_production_bot.bat      # Windows launcher
├── requirements.txt              # Python dependencies
├── data/                         # Data cache
├── logs/                         # Execution logs
└── reports/                      # Generated reports
```

## 🎓 How It Works

1. **Initialize** - Load DataManager and SMC Analyzer
2. **Connect** - Establish MT5 connection with retry logic
3. **Collect** - Fetch OHLCV data for all symbols/timeframes
4. **Analyze** - Run SMC analysis (Order Blocks, Market Structure)
5. **Report** - Generate CSV report with results

## 🔍 SMC Analysis

The bot analyzes:

- **Order Blocks** - Institutional buying/selling zones
- **Market Structure** - Trend identification (HH/HL or LH/LL)
- **Swing Points** - Key highs and lows
- **Multi-Timeframe Confluence** - Align timeframes

### Confidence Levels

- **🟢 High (75%+)** - Strong conviction
- **🟡 Medium (55-74%)** - Moderate conviction
- **⚪ Low (40-54%)** - Weak conviction
- **➡️ Neutral (<40%)** - No clear direction

## 📈 Production Features

- **Non-blocking operations** - Timeouts prevent hanging
- **Progress tracking** - See what's happening in real-time
- **Intelligent caching** - Avoid redundant API calls
- **Error recovery** - Continue on errors, don't crash
- **Professional logging** - Debug issues easily
- **Resource cleanup** - Proper shutdown and cleanup

## 🤝 Support

If you encounter issues:

1. Check the **logs/** directory
2. Review **error messages** in console
3. Verify **dependencies** are installed
4. Check **MT5 connection** status
5. Test with **single symbol** first

## 📝 License

This is a professional trading bot. Use at your own risk.

## ⚠️ Disclaimer

This bot is for **educational and research purposes** only. 

- NOT financial advice
- Past performance ≠ future results
- Trade at your own risk
- Use demo accounts first
- Understand the risks

---

**Built with ❤️ for professional traders**
