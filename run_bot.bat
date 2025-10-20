@echo off
REM ============================================================================
REM Production-Grade MT5 Trading Bot - Windows Launcher
REM ============================================================================

title MT5 Trading Bot - PRODUCTION
color 0A

echo.
echo =========================================================================
echo                   MT5 TRADING BOT - PRODUCTION MODE
echo =========================================================================
echo.
echo   This bot will:
echo   - Connect to MetaTrader 5
echo   - Collect real-time market data
echo   - Analyze using Smart Money Concepts
echo   - Generate trading bias reports
echo.
echo =========================================================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Python not found! Please install Python 3.8+
    pause
    exit /b 1
)

REM Run the bot
echo Starting bot...
echo.
python run_bot.py

REM Show completion
echo.
echo =========================================================================
echo                            BOT FINISHED
echo =========================================================================
echo.
pause
