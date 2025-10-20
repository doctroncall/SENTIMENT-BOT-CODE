# ✅ CURSOR SMC - ALL FILES ARE IN YOUR WORKSPACE ROOT

## 📍 You're Looking At Them Right Now!

All CURSOR-SMC files are in **the same folder** where you see:
- dashboard.py
- gui.py  
- run_bot.py
- etc.

Just **scroll through your file list** in Cursor's left sidebar!

---

## 📂 CURSOR-SMC Files (Look for these names):

### ⚡ Quick Start Files
```
install.bat              ← Install dependencies (double-click this first)
start.bat                ← Start the bot (double-click to trade)
test_connection.bat      ← Test MT5 connection
```

### 🐍 Python Files
```
main.py                  ← Main entry point
src/
├── mt5_connector.py     ← MT5 integration
├── smc_analyzer.py      ← SMC strategy
├── trading_bot.py       ← Trading logic
├── config_manager.py    ← Configuration
└── logger_setup.py      ← Logging
```

### ⚙️ Configuration
```
config_cursor_smc/
└── config.yaml          ← Edit this to set your symbols, timeframe, etc.
```

### 📖 Documentation
```
CURSOR_SMC_README.md     ← Full instructions
START_CURSOR_SMC.txt     ← Quick guide
```

### 📦 Dependencies
```
requirements_cursor_smc.txt  ← Python packages needed
```

---

## 🚀 How To Start (3 Steps)

### Step 1: Install
Double-click `install.bat` in your file list

### Step 2: Configure  
Open `config_cursor_smc/config.yaml` and edit:
```yaml
trading:
  symbols: ["EURUSD", "GBPUSD"]  # Your trading pairs
  timeframe: "H1"                # H1, H4, D1, etc.
  lot_size: 0.01                 # Position size
  risk_percent: 1.0              # 1% risk per trade
```

### Step 3: Start Trading
Double-click `start.bat` in your file list

---

## 🔍 Can't Find Them? 

**Look in your Cursor file explorer (left sidebar) for:**
- A file called `install.bat`
- A file called `start.bat`
- A file called `CURSOR_SMC_README.md`
- A folder called `src/` 
- A folder called `config_cursor_smc/`

**They're in the SAME PLACE as:**
- dashboard.py
- gui.py
- run_bot.py
- All your other files

---

## 📊 What The Bot Does

1. Connects to MetaTrader 5 (Windows)
2. Analyzes charts using Smart Money Concepts
3. Identifies Order Blocks and Fair Value Gaps
4. Generates BUY/SELL signals
5. Places trades with SL/TP automatically
6. Manages risk based on your settings

---

## ⚠️ Important

- Start with DEMO account first!
- Make sure MT5 is running before you start the bot
- Check logs in `logs/smc_bot.log`
- Press Ctrl+C to stop the bot

---

**All files are ready to use - just look for them in your file list!** 🎉
