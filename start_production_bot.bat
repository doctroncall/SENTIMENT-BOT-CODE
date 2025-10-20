@echo off
REM ============================================================================
REM Production MT5 Trading Bot - Startup Script (Windows)
REM ============================================================================
REM This script ensures all dependencies are installed and runs the bot with
REM proper error handling and logging.
REM
REM Usage:
REM   start_production_bot.bat [symbols]
REM
REM Examples:
REM   start_production_bot.bat                    REM Default symbols
REM   start_production_bot.bat GBPUSD,EURUSD      REM Custom symbols
REM ============================================================================

echo.
echo ================================================================================
echo                🤖 PRODUCTION MT5 TRADING BOT - STARTUP                        
echo ================================================================================
echo.

REM Check Python installation
echo [INFO] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Please install Python 3.8 or higher.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo [OK] %PYTHON_VERSION% found

REM Check dependencies
echo [INFO] Checking dependencies...

python -c "import pandas" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] pandas not installed. Installing...
    python -m pip install pandas numpy --quiet
    echo [OK] pandas installed
) else (
    echo [OK] pandas installed
)

python -c "import numpy" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] numpy not installed. Installing...
    python -m pip install numpy --quiet
    echo [OK] numpy installed
) else (
    echo [OK] numpy installed
)

REM Create necessary directories
echo [INFO] Creating necessary directories...
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "reports" mkdir reports
echo [OK] Directories ready

REM Check for run_bot.py
if not exist "run_bot.py" (
    echo [ERROR] run_bot.py not found in current directory!
    pause
    exit /b 1
)

echo [OK] All pre-flight checks passed!

REM Run the bot
echo.
echo ================================================================================
echo                     🚀 STARTING BOT...                                        
echo ================================================================================
echo.

REM Set environment variables for production
set PYTHONUNBUFFERED=1
set MT5_TIMEOUT_MS=30000

REM Parse command line arguments
set SYMBOLS=%1
if "%SYMBOLS%"=="" set SYMBOLS=GBPUSD,XAUUSD,EURUSD

REM Create log filename
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set LOG_FILE=logs\bot_run_%datetime:~0,8%_%datetime:~8,6%.log

echo [INFO] Running bot with symbols: %SYMBOLS%
echo [INFO] Logging to: %LOG_FILE%
echo.

REM Run the bot
python run_bot.py %SYMBOLS% 2>&1 | tee %LOG_FILE%

if %errorlevel% equ 0 (
    echo.
    echo ================================================================================
    echo [OK] Bot completed successfully!
    echo ================================================================================
) else (
    echo.
    echo ================================================================================
    echo [ERROR] Bot exited with error code: %errorlevel%
    echo ================================================================================
)

echo.
echo Press any key to exit...
pause >nul
