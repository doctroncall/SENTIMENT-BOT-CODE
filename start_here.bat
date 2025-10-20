@echo off
echo ========================================
echo   Trading Sentiment Analysis System
echo   Starting GUI...
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Python not found! Please install Python 3.x
    pause
    exit /b 1
)
echo [OK] Python found
python --version
echo.

REM Check if gui.py exists
if not exist gui.py (
    echo [X] gui.py not found in current directory!
    pause
    exit /b 1
)
echo [OK] gui.py found
echo.

echo Checking dependencies...
python -c "import streamlit" >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Streamlit not found! Installing...
    pip install streamlit
) else (
    echo [OK] Basic dependencies check complete
)
echo.

echo Starting GUI application...
echo.
echo ----------------------------------------
echo To close the application, close the GUI window
echo ----------------------------------------
echo.

REM Launch using streamlit (lowercase gui.py is the Streamlit version)
streamlit run gui.py

pause
