# 🚀 Quick Start - Trading Sentiment Analysis Bot

## ✅ **ONE COMMAND TO START EVERYTHING**

### Windows:
```batch
start_here.bat
```

### Linux/Mac:
```bash
./start_here.sh
```

---

## 📋 What It Does

The `start_here.bat` script is your **unified entry point** that:

1. ✅ **Checks Python** installation
2. ✅ **Verifies bot files** are present
3. ✅ **Installs dependencies** if missing
4. ✅ **Checks MT5** configuration (optional)
5. ✅ **Launches Streamlit GUI** automatically

**Everything starts with one command - no manual steps needed!**

---

## 🎯 First Time Setup

### Step 1: Clone/Download the Bot
```bash
git clone <your-repo>
cd <bot-directory>
```

### Step 2: (Optional) Set MT5 Credentials
Windows:
```batch
set MT5_LOGIN=your_account_number
set MT5_PASSWORD=your_password
set MT5_SERVER=your_broker_server
```

Linux/Mac:
```bash
export MT5_LOGIN=your_account_number
export MT5_PASSWORD=your_password
export MT5_SERVER=your_broker_server
```

### Step 3: Run the Bot
```batch
start_here.bat
```

**That's it!** The GUI will open in your browser automatically.

---

## 🖥️ What Happens When You Run It

### Console Output:
```
========================================
  TRADING SENTIMENT ANALYSIS BOT
========================================

  Unified Startup Script
  Starting all components...

========================================

[1/5] Checking Python...
[OK] Python found:
Python 3.11.0

[2/5] Checking bot files...
[OK] Core files found

[3/5] Checking dependencies...
[OK] Dependencies ready

[4/5] Checking MT5 status...
[OK] MT5 credentials found in environment

[5/5] Launching Trading Bot GUI...

========================================
  BOT IS STARTING...
========================================

The Streamlit GUI will open in your browser.
```

### Browser Opens Automatically:
- **URL:** http://localhost:8501
- **GUI:** 5 tabs (Home, Analysis, Health, Retrain, Running Status)
- **Ready to use!**

---

## 🏠 Using the GUI

Once the browser opens, you'll see **5 tabs**:

### 1. 🏠 **Home**
- Quick action buttons (Run Analysis, Verify, Retrain)
- System status (MT5, Predictions, Accuracy)
- Recent predictions table
- Symbol configuration

### 2. 📊 **Analysis**
- Run full analysis (all symbols)
- Run single symbol analysis
- View completed analyses
- Filter results

### 3. 🏥 **Health**
- System health check
- Component status
- Quick diagnostic tests

### 4. 🔄 **Retrain**
- View accuracy metrics
- Retrain the model
- Performance tracking

### 5. 📡 **Running Status**
- Live event log
- Second-by-second updates
- Auto-refresh

---

## 🛑 How to Stop the Bot

### Proper Shutdown:
1. **Close the browser tab** (GUI window)
2. **Go back to the console window**
3. **Press `Ctrl+C`**
4. **Confirm** when prompted

### Or:
- Just close the console window (less clean but works)

---

## ⚠️ Troubleshooting

### "Python not found"
**Solution:** Install Python 3.8+ from https://python.org/downloads/
- During installation, check "Add Python to PATH"

### "Streamlit not found"
**Solution:** The script will auto-install it, or run:
```bash
pip install streamlit
```

### "MT5 connection failed"
**Solution:**
1. Make sure MetaTrader 5 is running
2. You're logged in to your account
3. Automated trading is enabled (Tools → Options → Expert Advisors)

### "Browser doesn't open"
**Solution:** Manually open http://localhost:8501 in your browser

### "Port 8501 already in use"
**Solution:** Another Streamlit app is running
- Close other Streamlit instances
- Or the script will use a different port (8502, 8503, etc.)

---

## 📂 File Structure

```
your-bot-directory/
├── start_here.bat          ← Run this to start everything
├── gui.py                  ← Streamlit GUI (main interface)
├── dashboard.py            ← Core bot logic
├── data_manager.py         ← Data fetching
├── sentiment_engine.py     ← Analysis engine
├── verifier.py             ← Prediction verification
├── auto_retrain.py         ← Model retraining
├── requirements.txt        ← Dependencies list
└── ...other files...
```

---

## 💡 Tips

### Daily Workflow:
1. **Morning:** Run `start_here.bat`
2. **Use GUI:** Run analysis via Home tab
3. **Check results:** View in Analysis tab
4. **Evening:** Verify predictions (Verification in Home tab)
5. **Close:** Ctrl+C in console

### Best Practices:
- ✅ Keep the console window open while using the GUI
- ✅ Always use the GUI to control the bot
- ✅ Check Health tab if issues arise
- ✅ Monitor Running Status tab for live updates

### Performance:
- The bot auto-installs dependencies on first run
- Subsequent runs start faster
- MT5 connection is tested but not required for startup

---

## 🔗 Related Files

- **`start_here.bat`** - Main startup script (Windows)
- **`start_here.sh`** - Main startup script (Linux/Mac)
- **`launch_gui.bat`** - Alternative GUI launcher
- **`install_dependencies.bat`** - Manual dependency installer
- **`check_system.bat`** - System diagnostics

---

## ✅ Summary

**ONE COMMAND:**
```batch
start_here.bat
```

**EVERYTHING WORKS:**
- ✅ Checks system
- ✅ Installs what's needed
- ✅ Launches GUI
- ✅ Opens browser
- ✅ Ready to trade

**No manual setup, no configuration files to edit, no confusion.**

---

**Created:** 2025-10-20  
**Purpose:** Unified entry point for Trading Sentiment Analysis Bot  
**Platform:** Windows (Primary), Linux/Mac (via .sh version)  
**Status:** Production Ready ✅
