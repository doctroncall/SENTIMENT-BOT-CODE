@echo off
echo ========================================
echo MT5 Connection Test
echo ========================================
echo.

REM Check if venv exists
if not exist "venv\" (
    echo ERROR: Virtual environment not found!
    echo Please run install.bat first
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Create and run test script
echo import MetaTrader5 as mt5 > test_mt5.py
echo import sys >> test_mt5.py
echo. >> test_mt5.py
echo print("Testing MT5 connection...") >> test_mt5.py
echo print() >> test_mt5.py
echo. >> test_mt5.py
echo if not mt5.initialize(): >> test_mt5.py
echo     print("ERROR: Failed to initialize MT5") >> test_mt5.py
echo     print("Make sure MetaTrader 5 is installed and running") >> test_mt5.py
echo     error = mt5.last_error() >> test_mt5.py
echo     print(f"Error: {error}") >> test_mt5.py
echo     sys.exit(1) >> test_mt5.py
echo. >> test_mt5.py
echo print("SUCCESS: Connected to MT5!") >> test_mt5.py
echo print() >> test_mt5.py
echo. >> test_mt5.py
echo account = mt5.account_info() >> test_mt5.py
echo if account: >> test_mt5.py
echo     print(f"Account: {account.login}") >> test_mt5.py
echo     print(f"Server: {account.server}") >> test_mt5.py
echo     print(f"Balance: {account.balance} {account.currency}") >> test_mt5.py
echo     print(f"Leverage: 1:{account.leverage}") >> test_mt5.py
echo else: >> test_mt5.py
echo     print("Could not get account info") >> test_mt5.py
echo. >> test_mt5.py
echo print() >> test_mt5.py
echo print("Getting available symbols...") >> test_mt5.py
echo symbols = mt5.symbols_get() >> test_mt5.py
echo if symbols: >> test_mt5.py
echo     print(f"Total symbols: {len(symbols)}") >> test_mt5.py
echo     print("First 10 visible symbols:") >> test_mt5.py
echo     count = 0 >> test_mt5.py
echo     for s in symbols: >> test_mt5.py
echo         if s.visible: >> test_mt5.py
echo             print(f"  - {s.name}") >> test_mt5.py
echo             count += 1 >> test_mt5.py
echo             if count >= 10: >> test_mt5.py
echo                 break >> test_mt5.py
echo. >> test_mt5.py
echo mt5.shutdown() >> test_mt5.py
echo print() >> test_mt5.py
echo print("Test complete!") >> test_mt5.py

python test_mt5.py
del test_mt5.py

echo.
pause
