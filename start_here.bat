@echo off
REM ============================================================
REM Trading Sentiment Analysis Bot - Unified Startup
REM This is THE entry point - run this to start everything
REM ============================================================

title Trading Sentiment Analysis Bot - Starting...
color 0A

echo.
echo ========================================
echo   TRADING SENTIMENT ANALYSIS BOT
echo ========================================
echo.
echo   Unified Startup Script
echo   Starting all components...
echo.
echo ========================================
echo.

REM ==========================================
REM 1. Check Python Installation
REM ==========================================
echo [1/5] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo.
    echo [X] FAILED: Python not found!
    echo.
    echo Please install Python 3.8 or higher:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)
echo [OK] Python found:
python --version
echo.

REM ==========================================
REM 2. Check Critical Files
REM ==========================================
echo [2/5] Checking bot files...
if not exist gui.py (
    color 0C
    echo [X] FAILED: gui.py not found!
    echo Please ensure you're in the correct directory.
    pause
    exit /b 1
)
if not exist dashboard.py (
    color 0C
    echo [X] FAILED: dashboard.py not found!
    echo Core bot files are missing.
    pause
    exit /b 1
)
echo [OK] Core files found
echo.

REM ==========================================
REM 3. Check Dependencies
REM ==========================================
echo [3/5] Checking dependencies...
python -c "import streamlit" >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Streamlit not found. Installing...
    pip install streamlit
    if %errorlevel% neq 0 (
        color 0C
        echo [X] Failed to install Streamlit
        pause
        exit /b 1
    )
)

python -c "import pandas" >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Missing dependencies. Installing from requirements.txt...
    if exist requirements.txt (
        pip install -r requirements.txt
    ) else (
        pip install pandas openpyxl MetaTrader5 reportlab yfinance
    )
)
echo [OK] Dependencies ready
echo.

REM ==========================================
REM 4. Check MT5 Connection (Optional)
REM ==========================================
echo [4/5] Checking MT5 status...
if defined MT5_LOGIN (
    echo [OK] MT5 credentials found in environment
) else (
    echo [!] MT5 credentials not set (optional - can connect via GUI)
)
echo.

REM ==========================================
REM 5. Launch Streamlit GUI
REM ==========================================
echo [5/5] Launching Trading Bot GUI...
echo.
echo ========================================
echo   BOT IS STARTING...
echo ========================================
echo.
echo The Streamlit GUI will open in your browser.
echo.
echo IMPORTANT:
echo - Do NOT close this window
echo - Use the GUI to control the bot
echo - To stop: Close the GUI browser tab first,
echo   then press Ctrl+C here
echo.
echo ========================================
echo.

REM Change title to show running status
title Trading Sentiment Analysis Bot - RUNNING

REM Launch Streamlit (this will open browser automatically)
streamlit run gui.py --server.headless false

REM If streamlit exits, show message
echo.
echo ========================================
echo   BOT STOPPED
echo ========================================
echo.
pause
