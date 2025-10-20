@echo off
echo ========================================
echo   Symbol Fixer - Auto-discover MT5 Symbols
echo ========================================
echo.
echo This will connect to your MT5 broker and
echo automatically find the correct symbol names.
echo.
pause

python fix_symbols.py

echo.
echo ========================================
echo   Done!
echo ========================================
echo.
pause
