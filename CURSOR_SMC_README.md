# Cursor SMC Trading Bot - Files Located Here

All CURSOR-SMC files are now in this workspace root directory.

## 🚀 Quick Start (Windows)

### 1. Install (2 minutes)
```
Double-click: install.bat
```

### 2. Configure (2 minutes)
Edit `config_cursor_smc/config.yaml`:
```yaml
trading:
  symbols: ["EURUSD", "GBPUSD"]  # Your symbols
  timeframe: "H1"                # Your timeframe
  lot_size: 0.01                 # Your lot size
  risk_percent: 1.0              # Risk per trade
```

### 3. Test Connection (30 seconds)
```
Double-click: test_connection.bat
```

### 4. Start Trading (30 seconds)
```
Double-click: start.bat
```

## 📁 Files in This Workspace

### Core Python Modules (in `src/` folder)
- `src/mt5_connector.py` - MT5 connection & trading
- `src/smc_analyzer.py` - SMC analysis engine
- `src/trading_bot.py` - Main bot logic
- `src/config_manager.py` - Configuration handling
- `src/logger_setup.py` - Logging setup

### Windows Batch Files (in root)
- `install.bat` - Install dependencies
- `start.bat` - Start the bot
- `test_connection.bat` - Test MT5 connection

### Configuration
- `config_cursor_smc/config.yaml` - All settings

### Main Entry
- `main.py` - Run the bot

### Dependencies
- `requirements_cursor_smc.txt` - Python packages

## 🎯 What This Bot Does

1. **Connects to MT5** - Robust connection to MetaTrader 5 on Windows
2. **Analyzes Markets** - Uses Smart Money Concepts (Order Blocks, FVGs, Market Structure)
3. **Generates Signals** - Creates BUY/SELL signals based on SMC
4. **Executes Trades** - Places trades with proper SL/TP
5. **Manages Risk** - Calculates position sizes based on account risk

## ⚙️ Requirements

- Windows 10/11
- Python 3.8+
- MetaTrader 5 installed and running
- MT5 account (demo or live)

## 📊 Default Settings

- **Risk per trade:** 1% of account balance
- **Risk:Reward ratio:** 1:2
- **Max positions:** 3 simultaneous trades
- **Scan interval:** 5 minutes

All settings can be changed in `config_cursor_smc/config.yaml`

## 🛑 Stop the Bot

Press `Ctrl+C` in the console window.

## 📝 Logs

Check `logs/smc_bot.log` for detailed activity logs.

## ⚠️ Important

- Start with a **DEMO account** first
- Never risk more than you can afford to lose
- Monitor the bot regularly
- Review logs to understand decisions

## 🔧 Troubleshooting

**Bot won't start?**
- Run `install.bat` first
- Make sure MT5 is running

**No trades happening?**
- The bot waits for proper SMC setups (this is normal and good!)
- Check logs to see market analysis

**Connection errors?**
- Run `test_connection.bat`
- Ensure MT5 is open and logged in

---

**Ready to start?** Run `install.bat` first!
