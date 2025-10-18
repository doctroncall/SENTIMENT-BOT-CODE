# Windows Quick Start Guide

## 🚀 Getting Started on Windows

Welcome! This guide will help you get up and running with the Trading Sentiment Analysis System on Windows.

## 📋 Prerequisites

- **Windows 10 or later**
- **Python 3.8+** - [Download from python.org](https://www.python.org/downloads/)
  - ⚠️ Make sure to check "Add Python to PATH" during installation!

## 🎯 Quick Start (3 Easy Steps)

### Step 1: Check Your System
Double-click: **`START_HERE.bat`**

This opens a menu with all available options. Choose option **[3] Check System Requirements** to verify everything is set up correctly.

### Step 2: Install Dependencies (First Time Only)
From the START_HERE menu, choose option **[4] Install/Update Dependencies**

Or directly double-click: **`install_dependencies.bat`**

This will automatically install all required Python packages.

### Step 3: Launch the GUI
From the START_HERE menu, choose option **[1] Launch GUI**

Or directly double-click: **`launch_gui.bat`**

🎉 **You're ready to go!**

---

## 📁 Available Batch Files

### 🎮 Main Launcher
- **`START_HERE.bat`** - Main menu with all options
  - Launch GUI
  - Run command line analysis
  - Check system health
  - Install dependencies
  - Open reports folder
  - View system information

### 🖥️ Direct Launchers
- **`launch_gui.bat`** - Start the graphical interface (recommended)
- **`run_analysis.bat`** - Run analysis from command line
- **`open_reports.bat`** - Quick access to generated reports

### 🔧 Maintenance Tools
- **`install_dependencies.bat`** - Install/update Python packages
- **`check_system.bat`** - Comprehensive system health check
  - Verifies Python installation
  - Checks all required files
  - Validates Python packages
  - Creates necessary directories
  - Reports any issues

---

## 🎨 Using the GUI

Once you launch the GUI, you'll see 6 tabs:

### 📊 Analysis Tab
- Enter symbols (e.g., GBPUSD, XAUUSD, EURUSD)
- Select timeframes (D1, H4, H1)
- Set lookback period
- Click "▶ Run Analysis"
- View real-time logs

### 📈 Data Tab
- Fetch market data for any symbol
- Connect to MetaTrader 5
- View data statistics and previews

### ✓ Verification Tab
- Verify prediction accuracy
- Browse Excel log files
- View performance metrics

### 🔄 Retrain Tab
- Check model performance
- Set accuracy thresholds
- Trigger retraining when needed

### 📄 Reports Tab
- Browse generated reports
- Double-click to open
- Quick access to reports folder

### ⚙ Settings Tab
- Configure MT5 credentials
- Set default symbols and timeframes
- Manage file paths
- Save configuration

---

## 🔍 Troubleshooting

### Python not found?
1. Install Python from [python.org](https://www.python.org/downloads/)
2. During installation, check "Add Python to PATH"
3. Restart your computer
4. Run `check_system.bat` again

### Import errors or missing packages?
Run `install_dependencies.bat` to install all required packages.

### GUI won't start?
1. Run `check_system.bat` to diagnose issues
2. Check the error messages
3. Make sure tkinter is available (included with most Python installations)

### MT5 connection issues?
1. Make sure MetaTrader 5 is installed
2. Check your login credentials in Settings tab
3. Verify server name is correct
4. MT5 must be running for connection to work

---

## 📂 Project Structure

```
trading-sentiment-analysis/
├── START_HERE.bat              # Main menu launcher ⭐
├── launch_gui.bat              # GUI launcher
├── run_analysis.bat            # CLI launcher
├── install_dependencies.bat    # Dependency installer
├── check_system.bat           # System checker
├── open_reports.bat           # Reports folder opener
│
├── GUI.py                     # Main GUI application
├── dashboard.py               # Command line dashboard
├── data_manager.py            # Data fetching & caching
├── sentiment_engine.py        # Sentiment analysis engine
├── structure_analyzer.py      # Market structure analysis
├── verifier.py                # Prediction verification
├── auto_retrain.py           # Automatic model retraining
├── report_generator.py       # Report generation
│
├── config/                    # Configuration files
│   ├── gui_config.json       # GUI settings
│   └── rule_weights.json     # Model weights
│
├── data/                      # Cached market data
├── reports/                   # Generated reports
└── logs/                      # System logs
```

---

## 💡 Tips

1. **First Time Setup**: Always run `check_system.bat` first
2. **Regular Use**: Just double-click `START_HERE.bat` or `launch_gui.bat`
3. **Updates**: Run `install_dependencies.bat` after pulling new code
4. **Reports**: Use `open_reports.bat` for quick access to your reports
5. **Settings**: Configure your default symbols in the Settings tab to save time

---

## 🆘 Need Help?

1. Run `check_system.bat` for diagnostic information
2. Check the logs in the GUI for detailed error messages
3. Review the Analysis Log tab for operation details
4. Ensure all Python dependencies are installed

---

## ✅ Success Checklist

- [ ] Python 3.8+ installed with PATH configured
- [ ] Ran `check_system.bat` successfully
- [ ] Installed dependencies via `install_dependencies.bat`
- [ ] Launched GUI via `launch_gui.bat`
- [ ] Configured MT5 credentials (if using MT5)
- [ ] Ran first analysis successfully

---

**Happy Trading! 📈**
