# Testing Checklist

## ✅ Pre-Flight Checks (Completed)

- [x] All Python files compile without syntax errors
- [x] No linting errors found
- [x] Git repository is clean and committed
- [x] Requirements.txt created
- [x] Batch files created and tested (syntax)
- [x] Documentation created

## 🧪 Windows System Testing

### Phase 1: Initial Setup

- [ ] Clone/download repository to Windows machine
- [ ] Verify Python 3.8+ is installed
- [ ] Python is in system PATH
- [ ] Run `check_system.bat` - should show system status
- [ ] Run `install_dependencies.bat` - should install all packages
- [ ] Verify no errors during installation

### Phase 2: File Validation

- [ ] Verify all files are present:
  - [ ] 8 Python modules (.py files)
  - [ ] 6 Batch files (.bat files)
  - [ ] requirements.txt
  - [ ] WINDOWS_QUICKSTART.md
- [ ] Check directories are created:
  - [ ] config/
  - [ ] data/
  - [ ] reports/
  - [ ] logs/

### Phase 3: GUI Testing

#### Launch & Initialization
- [ ] Double-click `launch_gui.bat`
- [ ] GUI window opens without errors
- [ ] All 6 tabs are visible:
  - [ ] Analysis
  - [ ] Data
  - [ ] Verification
  - [ ] Retrain
  - [ ] Reports
  - [ ] Settings
- [ ] Status bar shows "Ready"

#### Analysis Tab
- [ ] Enter symbols (e.g., "GBPUSD, XAUUSD")
- [ ] Set timeframes (e.g., "D1, H4")
- [ ] Set lookback days (e.g., 30)
- [ ] Click "Run Analysis"
- [ ] Analysis log shows progress
- [ ] No errors during analysis
- [ ] Sentiment results are generated
- [ ] Excel log file created (sentiment_log.xlsx)

#### Data Tab
- [ ] Enter a symbol (e.g., "GBPUSD")
- [ ] Select timeframe (e.g., "H4")
- [ ] Set days (e.g., 30)
- [ ] Click "Fetch Data"
- [ ] Data is displayed in log
- [ ] Shows bar count and date range
- [ ] Data preview appears
- [ ] MT5 Connect button works (if MT5 installed)

#### Verification Tab
- [ ] Excel file path is correct
- [ ] Click "Run Verification"
- [ ] Verification completes without errors
- [ ] Click "Show Accuracy" displays statistics
- [ ] Accuracy percentage is reasonable

#### Retrain Tab
- [ ] Set accuracy threshold (e.g., 0.70)
- [ ] Set min samples (e.g., 10)
- [ ] Click "Check Performance"
- [ ] Shows current accuracy
- [ ] Indicates if retraining needed
- [ ] Click "Run Retrain" (if needed)
- [ ] Weights are updated in config/rule_weights.json

#### Reports Tab
- [ ] Reports directory shows up
- [ ] Click "Refresh List"
- [ ] Generated reports appear in list
- [ ] Double-click a report opens it
- [ ] "Open Folder" opens reports directory

#### Settings Tab
- [ ] All fields are editable
- [ ] Default symbols can be changed
- [ ] Default timeframes can be changed
- [ ] MT5 credentials can be entered
- [ ] Click "Save Configuration"
- [ ] Settings persist after restart
- [ ] "Reset to Defaults" works

### Phase 4: Command Line Testing

- [ ] Run `run_analysis.bat`
- [ ] Dashboard runs in console
- [ ] Analysis completes successfully
- [ ] Results are logged to Excel

### Phase 5: Batch File Testing

#### START_HERE.bat Menu
- [ ] Opens with menu displayed
- [ ] Option 1: Launches GUI
- [ ] Option 2: Runs command line analysis
- [ ] Option 3: Shows system check
- [ ] Option 4: Installs dependencies
- [ ] Option 5: Opens reports folder
- [ ] Option 6: Shows system information
- [ ] Option 7: Exits cleanly

#### check_system.bat
- [ ] Shows Python version
- [ ] Lists all core files
- [ ] Checks Python packages
- [ ] Reports installed versions
- [ ] Creates missing directories
- [ ] Shows summary status

#### open_reports.bat
- [ ] Opens reports folder in Explorer
- [ ] Creates folder if missing

### Phase 6: Integration Testing

#### MT5 Integration (if available)
- [ ] MT5 is installed and running
- [ ] Enter valid MT5 credentials in Settings
- [ ] Click "Connect MT5" in Data tab
- [ ] Connection succeeds
- [ ] Can fetch real market data
- [ ] Data appears in cache (data/ folder)

#### Full Analysis Workflow
- [ ] Run analysis on 2-3 symbols
- [ ] Check Excel log created
- [ ] Verify predictions logged
- [ ] Reports generated (PDF/TXT)
- [ ] Run verification on predictions
- [ ] Check retraining if accuracy low
- [ ] Verify updated weights

### Phase 7: Error Handling

- [ ] Try invalid symbol - graceful error message
- [ ] Try with no internet (yfinance fallback)
- [ ] Try with MT5 disconnected
- [ ] Try with missing Excel file
- [ ] Try with corrupted config file
- [ ] All errors display user-friendly messages
- [ ] No crashes or unhandled exceptions

### Phase 8: Performance Testing

- [ ] Analyze 5+ symbols simultaneously
- [ ] GUI remains responsive
- [ ] Progress updates in real-time
- [ ] Can view logs while running
- [ ] Memory usage is reasonable

### Phase 9: Data Persistence

- [ ] Close and reopen GUI
- [ ] Previous settings are loaded
- [ ] Excel log persists
- [ ] Reports are still available
- [ ] Cache files remain
- [ ] Configuration saved correctly

### Phase 10: Documentation Testing

- [ ] WINDOWS_QUICKSTART.md is clear
- [ ] Instructions are accurate
- [ ] All mentioned files exist
- [ ] Troubleshooting steps work

## 🐛 Issues Found

Document any issues discovered during testing:

| Issue # | Component | Description | Severity | Status |
|---------|-----------|-------------|----------|--------|
| | | | | |

## 📊 Test Results Summary

- Total Tests: ___
- Passed: ___
- Failed: ___
- Skipped: ___

## ✅ Sign-Off

- [ ] All critical tests passed
- [ ] Known issues documented
- [ ] System ready for production use

---

**Tester Name:** _______________  
**Date:** _______________  
**Python Version:** _______________  
**Windows Version:** _______________  
