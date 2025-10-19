@echo off
REM ============================================================
REM Trading Sentiment Analysis System - Dependency Installer
REM ============================================================

title Trading Sentiment Analysis - Install Dependencies

echo ========================================
echo   Trading Sentiment Analysis System
echo   Installing Dependencies...
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

REM Upgrade pip first
echo Step 1: Upgrading pip...
echo ----------------------------------------
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo WARNING: Failed to upgrade pip
    echo Continuing anyway...
)
echo.

REM Check if requirements.txt exists
if exist "requirements.txt" (
    echo Step 2: Installing from requirements.txt...
    echo ----------------------------------------
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install from requirements.txt
        echo.
        pause
        exit /b 1
    )
    echo.
    echo [OK] All dependencies from requirements.txt installed
    echo.
) else (
    echo Step 2: Installing core dependencies...
    echo ----------------------------------------
    echo.
    
    echo Installing pandas...
    python -m pip install pandas
    
    echo Installing numpy...
    python -m pip install numpy
    
    echo Installing openpyxl (for Excel support)...
    python -m pip install openpyxl
    
    echo Installing MetaTrader5...
    python -m pip install MetaTrader5
    
    echo Installing yfinance (optional - for fallback data)...
    python -m pip install yfinance
    
    echo Installing reportlab (optional - for PDF reports)...
    python -m pip install reportlab
    
    echo.
    echo [OK] Core dependencies installed
    echo.
)

REM Verify installations
echo Step 3: Verifying installations...
echo ----------------------------------------
python -c "import pandas; print('pandas version:', pandas.__version__)"
python -c "import numpy; print('numpy version:', numpy.__version__)"
python -c "import openpyxl; print('openpyxl version:', openpyxl.__version__)"

echo.
echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo You can now run:
echo   - launch_gui.bat       (to start the GUI)
echo   - run_analysis.bat     (for command line analysis)
echo.

pause
