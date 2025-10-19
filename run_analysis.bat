@echo off
REM ============================================================
REM Trading Sentiment Analysis System - Command Line Analysis
REM ============================================================

title Trading Sentiment Analysis - Command Line

echo ========================================
echo   Trading Sentiment Analysis System
echo   Running Command Line Analysis...
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from python.org
    echo.
    pause
    exit /b 1
)

echo [OK] Python found
python --version
echo.

REM Check if dashboard.py exists
if not exist "dashboard.py" (
    echo ERROR: dashboard.py not found in current directory
    echo Please run this script from the project directory
    echo.
    pause
    exit /b 1
)

echo [OK] dashboard.py found
echo.

REM Launch the dashboard
echo Starting analysis...
echo.
echo ----------------------------------------
echo Press Ctrl+C to stop the analysis
echo ----------------------------------------
echo.

python dashboard.py

REM Check exit code
if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo ERROR: Analysis exited with error code %errorlevel%
    echo ========================================
    echo.
)

echo.
echo Analysis complete
pause
