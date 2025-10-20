@echo off
echo ========================================
echo   List All MT5 Symbols
echo ========================================
echo.
echo This will show all available symbols
echo in your MT5 broker account.
echo.
pause

python list_mt5_symbols.py --all

echo.
echo ========================================
echo   Done!
echo ========================================
echo.
pause
