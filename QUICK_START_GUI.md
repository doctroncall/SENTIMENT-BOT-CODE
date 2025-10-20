# 🚀 Quick Start Guide - New Streamlit GUI

## Launch the Dashboard

### Option 1: Direct Launch
```bash
streamlit run gui.py
```

### Option 2: Using Launch Script
```bash
./launch_streamlit_gui.sh
```

### Option 3: Windows
```bash
launch_gui.bat
```

---

## 🎯 First Time Setup

### 1. Check MT5 Connection
- Look at the top of the dashboard for the connection status
- If showing 🔴 or 🟡, click "🔌 Connect MT5"
- Verify connection details in the expandable section

### 2. Configure Symbols
- Open the sidebar (⚙️ Configuration)
- Enter your symbols in the text area (e.g., GBPUSD, XAUUSD, EURUSD)
- Click "✅ Apply Symbols"

### 3. Run Your First Analysis
- Go to the "📊 Analysis" tab
- Click "▶️ Run Full Analysis"
- Wait for completion (you'll see a success message)

### 4. View Results
- Go to "🏠 Home" tab to see recent predictions
- Check "📄 Reports" tab for detailed reports
- Use "✅ Verification" tab to verify accuracy

---

## 🎨 Key Features at a Glance

### MT5 Connection Status (Top of Page)
```
🟢 Connected    → MT5 is connected and ready
🟡 Disconnected → MT5 is available but not connected
🔴 Error        → MT5 connection error
⚠️ Disabled     → MT5 is not enabled
```

### System Metrics Dashboard
- **Total Predictions**: Number of analyses run
- **Accuracy**: Percentage of correct predictions
- **Tracked Symbols**: Number of symbols being monitored
- **MT5 Connection**: Live connection status

### Tab Navigation
| Tab | Purpose | Key Actions |
|-----|---------|-------------|
| 🏠 Home | Overview & Quick Start | View recent predictions |
| 📊 Analysis | Run Market Analysis | Full or single symbol analysis |
| ✅ Verification | Verify & Retrain | Check accuracy, retrain model |
| 📄 Reports | View Reports | Browse and download reports |
| 🏥 Health | System Health | Run health checks |

---

## ⚙️ Configuration Options

### Sidebar Settings

#### Trading Symbols
- Add/remove symbols
- Comma or newline separated
- Example: `GBPUSD, EURUSD, XAUUSD`

#### Settings
- **Allow synthetic fallback**: Use synthetic data when MT5/Yahoo fail
- **Show operation logs**: Display detailed logs for operations
- **Auto-refresh data**: Enable automatic data updates

#### Quick Actions
- **Refresh Dashboard**: Reload all data
- **Clear Cache**: Clear Streamlit cache

---

## 🔧 Common Tasks

### Connect to MT5
1. Ensure MT5 terminal is running on your computer
2. Click "🔌 Connect MT5" button at the top
3. Wait for confirmation
4. Status should change to 🟢 Connected

### Run Analysis
1. Ensure MT5 is connected (🟢)
2. Go to "📊 Analysis" tab
3. Choose:
   - **Full Analysis**: All configured symbols
   - **Single Analysis**: Specific symbol
4. Click the run button
5. Wait for completion

### Verify Predictions
1. Go to "✅ Verification" tab
2. Click "▶️ Verify Predictions"
3. View accuracy metrics
4. Optionally run "▶️ Run Retraining" to improve model

### View Reports
1. Go to "📄 Reports" tab
2. Select report from dropdown
3. Click "⬇️ Download" to save
4. Expand "👁️ Preview Report" to view inline

### Check System Health
1. Go to "🏥 Health" tab
2. Click "🔍 Run Health Check"
3. Review results
4. Check system information below

---

## 💡 Tips & Best Practices

### Connection Management
- ✅ Always check MT5 connection before running analysis
- ✅ Keep MT5 terminal open while using the dashboard
- ✅ Use the disconnect button when switching accounts

### Analysis Workflow
- ✅ Start with a small number of symbols (2-3)
- ✅ Run single symbol analysis to test first
- ✅ Check reports after each analysis
- ✅ Verify predictions regularly to improve accuracy

### Performance
- ✅ Enable logs only when troubleshooting
- ✅ Clear cache periodically for optimal performance
- ✅ Close unused browser tabs

### Monitoring
- ✅ Check system metrics regularly
- ✅ Run health checks before important operations
- ✅ Review verification accuracy by symbol

---

## 🐛 Troubleshooting

### MT5 Won't Connect
**Problem**: Status shows 🔴 or connection fails

**Solutions**:
1. Ensure MT5 terminal is running
2. Check MT5 credentials in connection details
3. Verify MT5 server is correct
4. Try disconnecting and reconnecting

### No Data / Empty Results
**Problem**: Analysis completes but shows no data

**Solutions**:
1. Verify MT5 connection is active (🟢)
2. Check symbols are valid for your broker
3. Enable "Allow synthetic fallback" in settings
4. Check operation logs for errors

### Analysis Fails
**Problem**: Analysis button shows error

**Solutions**:
1. Run health check (🏥 Health tab)
2. Check operation logs
3. Verify sufficient historical data
4. Try single symbol analysis first

### Reports Not Showing
**Problem**: Reports tab is empty

**Solutions**:
1. Run an analysis first
2. Check that `reports/` directory exists
3. Verify write permissions

---

## 📊 Understanding the Metrics

### Accuracy
- Calculated from verified predictions
- Shows percentage of correct directional predictions
- Updated after running verification

### Confidence
- Model's confidence in prediction (0-100%)
- Higher confidence = stronger signal
- Used in weighted scoring

### Weighted Score
- Combined score considering all indicators
- Positive = Bullish bias
- Negative = Bearish bias
- Range: typically -5 to +5

### Verification Status
- ✅ True: Prediction was correct
- ❌ False: Prediction was incorrect
- ⏳ Pending: Not yet verified

---

## 🎓 Advanced Features

### Custom Symbol Analysis
- Use the single symbol analysis for on-demand checks
- Great for responding to market events
- Results are saved to the same log

### Batch Operations
- Configure multiple symbols in sidebar
- Run full analysis for all at once
- Review results per symbol in verification tab

### Report Downloads
- PDF reports for sharing
- TXT reports for text analysis
- All reports include timestamp and full analysis

### Health Monitoring
- Comprehensive system checks
- Component-by-component status
- Helps identify issues quickly

---

## 🔐 Security Notes

- MT5 credentials are stored in environment variables
- Connection details visible only in expanded section
- Reports contain no sensitive credential information
- Always use demo accounts for testing

---

## 📞 Support & Help

### In-Dashboard Help
1. Hover over toggles/buttons for tooltips
2. Check operation logs for detailed errors
3. Run health check for system diagnostics

### External Resources
- Check `GUI_IMPROVEMENTS.md` for detailed feature list
- Review `dashboard.py` for core functionality
- Examine reports for analysis details

---

## 🎉 You're Ready!

The new GUI is designed to be intuitive and powerful. Start with the basics:
1. ✅ Connect to MT5
2. ✅ Configure symbols
3. ✅ Run analysis
4. ✅ Review results

Then explore advanced features like verification, retraining, and health monitoring.

**Happy Trading! 📈🚀**
