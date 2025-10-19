@echo off
REM ============================================================
REM Trading Sentiment Analysis System - Main Menu
REM ============================================================

title Trading Sentiment Analysis - Main Menu

:menu
cls
echo ========================================
echo   TRADING SENTIMENT ANALYSIS SYSTEM
echo ========================================
echo.
echo   Main Menu - Choose an option:
echo.
echo   [1] Launch GUI (Recommended)
echo   [2] Run Command Line Analysis
echo   [3] Check System Requirements
echo   [4] Install/Update Dependencies
echo   [5] Open Reports Folder
echo   [6] View System Information
echo   [7] Exit
echo.
echo ========================================
echo.

set /p choice="Enter your choice (1-7): "

if "%choice%"=="1" goto launch_gui
if "%choice%"=="2" goto run_analysis
if "%choice%"=="3" goto check_system
if "%choice%"=="4" goto install_deps
if "%choice%"=="5" goto open_reports
if "%choice%"=="6" goto system_info
if "%choice%"=="7" goto exit

echo.
echo Invalid choice. Please enter a number between 1 and 7.
timeout /t 2 >nul
goto menu

:launch_gui
cls
echo Launching GUI...
echo.
call launch_gui.bat
goto menu

:run_analysis
cls
echo Running command line analysis...
echo.
call run_analysis.bat
goto menu

:check_system
cls
echo Running system check...
echo.
call check_system.bat
goto menu

:install_deps
cls
echo Installing dependencies...
echo.
call install_dependencies.bat
goto menu

:open_reports
cls
echo Opening reports folder...
echo.
call open_reports.bat
goto menu

:system_info
cls
echo ========================================
echo   SYSTEM INFORMATION
echo ========================================
echo.
echo Python Version:
python --version 2>nul
if %errorlevel% neq 0 (
    echo Python not found in PATH
) else (
    echo.
    echo Python Location:
    where python
    echo.
    echo Installed Packages:
    python -m pip list | findstr /i "pandas numpy openpyxl MetaTrader5 reportlab yfinance"
)
echo.
echo Current Directory:
cd
echo.
echo ========================================
echo.
pause
goto menu

:exit
cls
echo.
echo Thank you for using Trading Sentiment Analysis System!
echo.
timeout /t 2 >nul
exit
