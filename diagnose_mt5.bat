@echo off
REM MT5 Connection Diagnostics
REM Run this to diagnose MT5 connection issues

echo.
echo ========================================
echo   MT5 Connection Diagnostics
echo ========================================
echo.
echo Running diagnostic checks...
echo.

python test_mt5_diagnostics.py

echo.
echo ========================================
echo   Diagnostics Complete
echo ========================================
echo.
echo Press any key to exit...
pause >nul
