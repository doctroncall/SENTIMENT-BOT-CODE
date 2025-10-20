@echo off
echo ========================================
echo SMC Trading Bot - Starting...
echo ========================================
echo.

REM Check if venv exists
if not exist "venv\" (
    echo ERROR: Virtual environment not found!
    echo Please run install.bat first
    pause
    exit /b 1
)

REM Check if MT5 is running
tasklist /FI "IMAGENAME eq terminal64.exe" 2>NUL | find /I /N "terminal64.exe">NUL
if errorlevel 1 (
    echo WARNING: MetaTrader 5 doesn't appear to be running!
    echo Please start MT5 before running the bot
    echo.
    echo Press any key to continue anyway, or Ctrl+C to exit
    pause >nul
)

REM Activate virtual environment and run bot
call venv\Scripts\activate.bat

echo Starting SMC Trading Bot...
echo Press Ctrl+C to stop the bot
echo.

python main.py

echo.
echo Bot stopped.
pause
