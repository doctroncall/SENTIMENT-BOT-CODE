@echo off
REM ============================================================
REM Trading Sentiment Analysis System - GUI Launcher
REM ============================================================

title Trading Sentiment Analysis GUI

echo ========================================
echo   Trading Sentiment Analysis System
echo   Starting GUI...
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

REM Check if GUI.py exists
if not exist "GUI.py" (
    echo ERROR: GUI.py not found in current directory
    echo Please run this script from the project directory
    echo.
    pause
    exit /b 1
)

echo [OK] GUI.py found
echo.

REM Check for required modules (basic check)
echo Checking dependencies...
python -c "import tkinter" >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: tkinter not available
    echo GUI may not work properly
    echo.
)

python -c "import pandas" >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: pandas not installed
    echo Please run install_dependencies.bat first
    echo.
)

echo [OK] Basic dependencies check complete
echo.

REM Launch the GUI
echo Starting GUI application...
echo.
echo ----------------------------------------
echo To close the application, close the GUI window
echo ----------------------------------------
echo.

python GUI.py

REM Check exit code
if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo ERROR: GUI exited with error code %errorlevel%
    echo ========================================
    echo.
    pause
    exit /b %errorlevel%
)

echo.
echo GUI closed successfully
pause
