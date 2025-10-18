@echo off
REM ============================================================
REM Trading Sentiment Analysis System - System Check
REM ============================================================

title Trading Sentiment Analysis - System Check

echo ========================================
echo   Trading Sentiment Analysis System
echo   System Health Check
echo ========================================
echo.

REM Check Python
echo [1/7] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] Python is not installed or not in PATH
    set /a errors+=1
) else (
    python --version
    echo [OK] Python found
)
echo.

REM Check core files
echo [2/7] Checking core files...
set missing_files=0

if not exist "GUI.py" (
    echo [FAIL] GUI.py not found
    set /a missing_files+=1
) else (
    echo [OK] GUI.py found
)

if not exist "dashboard.py" (
    echo [FAIL] dashboard.py not found
    set /a missing_files+=1
) else (
    echo [OK] dashboard.py found
)

if not exist "data_manager.py" (
    echo [FAIL] data_manager.py not found
    set /a missing_files+=1
) else (
    echo [OK] data_manager.py found
)

if not exist "sentiment_engine.py" (
    echo [FAIL] sentiment_engine.py not found
    set /a missing_files+=1
) else (
    echo [OK] sentiment_engine.py found
)

if not exist "verifier.py" (
    echo [FAIL] verifier.py not found
    set /a missing_files+=1
) else (
    echo [OK] verifier.py found
)

if %missing_files% gtr 0 (
    echo [WARNING] %missing_files% core file(s) missing
)
echo.

REM Check Python packages
echo [3/7] Checking Python packages...

python -c "import pandas" >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] pandas not installed
    set /a errors+=1
) else (
    python -c "import pandas; print('[OK] pandas version:', pandas.__version__)"
)

python -c "import numpy" >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] numpy not installed
    set /a errors+=1
) else (
    python -c "import numpy; print('[OK] numpy version:', numpy.__version__)"
)

python -c "import openpyxl" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] openpyxl not installed (Excel support will be limited)
) else (
    python -c "import openpyxl; print('[OK] openpyxl version:', openpyxl.__version__)"
)

python -c "import MetaTrader5" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] MetaTrader5 not installed (MT5 features will be disabled)
) else (
    echo [OK] MetaTrader5 installed
)

python -c "import tkinter" >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] tkinter not available (GUI will not work)
    set /a errors+=1
) else (
    echo [OK] tkinter available
)

echo.

REM Check directories
echo [4/7] Checking directories...

if not exist "data" (
    echo [INFO] Creating data directory...
    mkdir data
)
echo [OK] data directory exists

if not exist "config" (
    echo [INFO] Creating config directory...
    mkdir config
)
echo [OK] config directory exists

if not exist "reports" (
    echo [INFO] Creating reports directory...
    mkdir reports
)
echo [OK] reports directory exists

if not exist "logs" (
    echo [INFO] Creating logs directory...
    mkdir logs
)
echo [OK] logs directory exists

echo.

REM Check configuration files
echo [5/7] Checking configuration files...

if not exist "config\rule_weights.json" (
    echo [INFO] rule_weights.json will be created on first run
) else (
    echo [OK] rule_weights.json exists
)

if not exist "config\gui_config.json" (
    echo [INFO] gui_config.json will be created on first run
) else (
    echo [OK] gui_config.json exists
)

echo.

REM Check Excel log file
echo [6/7] Checking data files...

if not exist "sentiment_log.xlsx" (
    echo [INFO] sentiment_log.xlsx will be created on first analysis
) else (
    echo [OK] sentiment_log.xlsx exists
)

echo.

REM Summary
echo [7/7] System Check Summary
echo ----------------------------------------

if defined errors (
    echo [WARNING] System check found %errors% error(s)
    echo Please run install_dependencies.bat to install missing packages
) else (
    echo [OK] All critical checks passed!
    echo System is ready to use
)

echo.
echo ========================================
echo   System Check Complete
echo ========================================
echo.
echo Available launchers:
echo   - launch_gui.bat           (Start GUI)
echo   - run_analysis.bat         (Run analysis from command line)
echo   - install_dependencies.bat (Install missing packages)
echo.

pause
