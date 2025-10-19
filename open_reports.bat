@echo off
REM ============================================================
REM Trading Sentiment Analysis System - Open Reports Folder
REM ============================================================

title Trading Sentiment Analysis - Reports

echo ========================================
echo   Opening Reports Folder...
echo ========================================
echo.

REM Check if reports directory exists
if not exist "reports" (
    echo Reports directory does not exist yet.
    echo Creating reports directory...
    mkdir reports
    echo.
    echo Reports directory created.
    echo Run an analysis first to generate reports.
    echo.
)

REM Open the reports folder
start "" "reports"

echo Reports folder opened in File Explorer
echo.

timeout /t 2 >nul
