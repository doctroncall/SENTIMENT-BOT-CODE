# Production-Grade MT5 Trading Bot

## 🚀 Quick Start

### Windows
```bash
run_bot.bat
```

### Linux/Mac
```bash
python run_bot.py
```

## 📊 What This Bot Does

1. **Connects to MetaTrader 5**
   - Uses your configured MT5 credentials
   - Automatically retries connection if needed
   - Shows real-time connection status

2. **Collects Market Data**
   - Fetches OHLCV data for multiple symbols
   - Analyzes multiple timeframes (D1, H4, H1)
   - Shows progress for each symbol/timeframe
   - Caches data for faster subsequent runs

3. **Analyzes Using Smart Money Concepts (SMC)**
   - Detects order blocks
   - Analyzes market structure
   - Calculates trading bias
   - Provides confidence levels

4. **Generates Reports**
   - CSV file with all results
   - Trading bias for each symbol
   - Confidence scores
   - Timestamps for tracking

## 🎯 Console Output Example

```
═══════════════════════════════════════════════════════════════════
                  🤖 PRODUCTION MT5 TRADING BOT
═══════════════════════════════════════════════════════════════════

[1/5] Initializing components...
  ✅ DataManager loaded
  ✅ SMC Analyzer loaded

[2/5] Connecting to MetaTrader 5...
  ⏳ Establishing connection...
     Server: ExnessKE-MT5Trial9
     Account: 211744072
  ✅ Connected to MT5 successfully!

[3/5] Collecting market data from MT5...

  Time     | Status Symbol     | TF    | Bars
  ------------------------------------------------------------
  14:32:15 | ✅ GBPUSD      | D1    |   250 bars
  14:32:16 | ✅ GBPUSD      | H4    |  1500 bars
  14:32:17 | ✅ GBPUSD      | H1    |  2160 bars
  14:32:19 | ✅ XAUUSD      | D1    |   250 bars
  14:32:20 | ✅ XAUUSD      | H4    |  1500 bars
  14:32:21 | ✅ XAUUSD      | H1    |  2160 bars

  ✅ Data collection complete: 2/2 symbols

[4/5] Analyzing market structure (SMC)...

  Analyzing 2 symbols...
  Symbol     | Bias     |   Confidence
  ----------------------------------------
  🟢 GBPUSD     | 📈 BULLISH  |  78.5% confidence
  🟡 XAUUSD     | 📉 BEARISH  |  62.3% confidence

  ✅ Analysis complete: 2/2 symbols

[5/5] Generating report...
  ✅ CSV report saved: bot_results_20251020_143225.csv

  📊 Summary:
     Total analyzed: 2
     📈 Bullish: 1
     📉 Bearish: 1
     ➡️ Neutral: 0
     🟢 High confidence (75%+): 1

═══════════════════════════════════════════════════════════════════
                   ✅ BOT COMPLETED SUCCESSFULLY
═══════════════════════════════════════════════════════════════════
  ⏱️ Total time: 12.3 seconds
  📊 Symbols processed: 2
  ✅ Success!
```

## ⚙️ Configuration

### Symbols
Edit `run_bot.py` to change symbols:
```python
symbols = ["GBPUSD", "XAUUSD", "EURUSD", "USDJPY"]
```

Or pass via command line:
```bash
python run_bot.py GBPUSD,EURUSD
```

### Timeframes
Edit `run_bot.py`:
```python
timeframes = ["D1", "H4", "H1", "M15"]
```

### MT5 Credentials
Set environment variables:
```bash
export MT5_LOGIN=your_account
export MT5_PASSWORD=your_password
export MT5_SERVER=your_server
```

Or edit `data_manager.py` (lines 49-51).

## 📁 Output Files

- `bot_results_YYYYMMDD_HHMMSS.csv` - Analysis results
- `data/SYMBOL_TF.csv` - Cached market data
- `logs/mt5_connector_YYYYMMDD.log` - Connection logs

## 🔧 Troubleshooting

### Bot hangs or freezes
- **Fixed!** The production bot now shows real-time progress
- If it still hangs, check MT5 connection
- Ensure terminal is running

### No data collected
- Verify MT5 credentials
- Check if symbols are available on your broker
- Try with different symbols

### Connection failed
- Ensure MetaTrader 5 terminal is installed
- Verify credentials in environment or code
- Check server name is correct

## 🎯 Production Features

✅ Real-time progress indicators
✅ Graceful error handling
✅ Automatic retry logic
✅ Data caching for speed
✅ Clean console output
✅ Professional logging
✅ CSV report generation
✅ Multiple symbol support
✅ Multi-timeframe analysis
✅ Smart Money Concepts (SMC)

## 📈 Next Steps

After running the bot:

1. **Check Results**: Open the CSV file
2. **Review Analysis**: Look at bias and confidence
3. **Take Action**: Use bias for your trading decisions
4. **Run Regularly**: Schedule bot runs for updated analysis

## 🤝 Support

For issues or questions:
- Check logs in `logs/` directory
- Review error messages in console
- Verify MT5 connection manually

---

**Made with ❤️ for professional traders**
