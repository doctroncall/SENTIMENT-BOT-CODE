#!/usr/bin/env python3
"""
MT5 Connection Test Script

Run this to verify your MT5 setup works correctly with Python/Streamlit
Usage: python test_mt5_connection.py
"""

import os
import sys
from datetime import datetime, timedelta

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_success(msg):
    print(f"{GREEN}✅ {msg}{RESET}")

def print_error(msg):
    print(f"{RED}❌ {msg}{RESET}")

def print_warning(msg):
    print(f"{YELLOW}⚠️  {msg}{RESET}")

def print_info(msg):
    print(f"{BLUE}ℹ️  {msg}{RESET}")

def test_mt5_import():
    """Test 1: Can we import MetaTrader5?"""
    print("\n" + "="*60)
    print("TEST 1: MetaTrader5 Package")
    print("="*60)
    
    try:
        import MetaTrader5 as mt5
        version = mt5.version()
        print_success(f"MetaTrader5 package found")
        print_info(f"Version: {version}")
        return True, mt5
    except ImportError:
        print_error("MetaTrader5 package not installed")
        print_info("Install with: pip install MetaTrader5")
        return False, None

def test_mt5_initialize(mt5):
    """Test 2: Can we initialize MT5?"""
    print("\n" + "="*60)
    print("TEST 2: MT5 Initialization")
    print("="*60)
    
    # Try with path from environment
    mt5_path = os.getenv("MT5_PATH", r"C:\Program Files\MetaTrader 5\terminal64.exe")
    
    print_info(f"Attempting to initialize MT5...")
    if mt5_path and os.path.exists(mt5_path):
        print_info(f"Using path: {mt5_path}")
        initialized = mt5.initialize(mt5_path)
    else:
        print_info("Using auto-detection")
        initialized = mt5.initialize()
    
    if not initialized:
        error = mt5.last_error()
        print_error(f"Initialization failed: {error}")
        print_warning("Make sure MT5 terminal is running!")
        return False
    
    print_success("MT5 initialized successfully")
    return True

def test_terminal_info(mt5):
    """Test 3: Get terminal information"""
    print("\n" + "="*60)
    print("TEST 3: Terminal Information")
    print("="*60)
    
    try:
        terminal_info = mt5.terminal_info()
        if terminal_info is None:
            print_error("Could not get terminal info")
            return False
        
        print_success("Terminal information retrieved")
        print(f"  Name: {terminal_info.name}")
        print(f"  Company: {terminal_info.company}")
        print(f"  Path: {terminal_info.path}")
        print(f"  Connected: {terminal_info.connected}")
        print(f"  Trade Allowed: {terminal_info.trade_allowed}")
        
        if not terminal_info.connected:
            print_warning("Terminal not connected to broker!")
            return False
        
        return True
    except Exception as e:
        print_error(f"Error getting terminal info: {e}")
        return False

def test_account_info(mt5):
    """Test 4: Get account information"""
    print("\n" + "="*60)
    print("TEST 4: Account Information")
    print("="*60)
    
    try:
        account_info = mt5.account_info()
        if account_info is None:
            print_warning("Not logged in to any account")
            print_info("Login through MT5 terminal first")
            return False
        
        print_success("Account information retrieved")
        print(f"  Login: {account_info.login}")
        print(f"  Server: {account_info.server}")
        print(f"  Company: {account_info.company}")
        print(f"  Balance: {account_info.balance}")
        print(f"  Currency: {account_info.currency}")
        
        return True
    except Exception as e:
        print_error(f"Error getting account info: {e}")
        return False

def test_symbols(mt5):
    """Test 5: Get available symbols"""
    print("\n" + "="*60)
    print("TEST 5: Available Symbols")
    print("="*60)
    
    try:
        symbols = mt5.symbols_get()
        if symbols is None or len(symbols) == 0:
            print_error("No symbols available")
            return False
        
        print_success(f"Found {len(symbols)} symbols")
        print_info("First 10 symbols:")
        for symbol in symbols[:10]:
            print(f"  - {symbol.name}")
        
        return True
    except Exception as e:
        print_error(f"Error getting symbols: {e}")
        return False

def test_data_fetch(mt5):
    """Test 6: Fetch historical data"""
    print("\n" + "="*60)
    print("TEST 6: Data Fetching")
    print("="*60)
    
    test_symbols = ["EURUSD", "GBPUSD", "XAUUSD"]
    
    for symbol in test_symbols:
        try:
            # Try to get symbol info first
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                print_warning(f"{symbol} not available from your broker")
                continue
            
            # Fetch last 10 daily bars
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 10)
            
            if rates is None or len(rates) == 0:
                print_warning(f"No data for {symbol}")
                continue
            
            print_success(f"Fetched {len(rates)} bars for {symbol}")
            print(f"  Latest close: {rates[-1]['close']:.5f}")
            print(f"  Date: {datetime.fromtimestamp(rates[-1]['time'])}")
            return True  # At least one symbol worked
            
        except Exception as e:
            print_warning(f"Error fetching {symbol}: {e}")
    
    print_error("Could not fetch data for any test symbol")
    return False

def test_streamlit_compatibility():
    """Test 7: Check Streamlit compatibility"""
    print("\n" + "="*60)
    print("TEST 7: Streamlit Compatibility")
    print("="*60)
    
    try:
        import streamlit
        print_success("Streamlit is installed")
        print_info(f"Version: {streamlit.__version__}")
    except ImportError:
        print_warning("Streamlit not installed")
        print_info("Install with: pip install streamlit")
    
    try:
        import pandas
        print_success("Pandas is installed")
        print_info(f"Version: {pandas.__version__}")
    except ImportError:
        print_error("Pandas not installed (required!)")
        return False
    
    return True

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🔌 MT5 + STREAMLIT CONNECTION TEST")
    print("="*60)
    print("This script tests if your MT5 setup will work with Streamlit")
    print("")
    
    results = []
    
    # Test 1: Import
    success, mt5 = test_mt5_import()
    results.append(("MetaTrader5 Package", success))
    if not success:
        print_error("\nCannot proceed without MetaTrader5 package!")
        sys.exit(1)
    
    # Test 2: Initialize
    success = test_mt5_initialize(mt5)
    results.append(("MT5 Initialization", success))
    if not success:
        print_error("\nCannot proceed - MT5 initialization failed!")
        print_info("Make sure:")
        print_info("1. MT5 terminal is installed")
        print_info("2. MT5 terminal is running")
        print_info("3. Path is correct (if specified)")
        mt5.shutdown()
        sys.exit(1)
    
    # Test 3: Terminal Info
    success = test_terminal_info(mt5)
    results.append(("Terminal Info", success))
    
    # Test 4: Account Info
    success = test_account_info(mt5)
    results.append(("Account Info", success))
    
    # Test 5: Symbols
    success = test_symbols(mt5)
    results.append(("Symbol List", success))
    
    # Test 6: Data Fetch
    success = test_data_fetch(mt5)
    results.append(("Data Fetching", success))
    
    # Test 7: Streamlit
    success = test_streamlit_compatibility()
    results.append(("Streamlit Compatibility", success))
    
    # Cleanup
    mt5.shutdown()
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        if success:
            print_success(f"{test_name}")
            passed += 1
        else:
            print_error(f"{test_name}")
    
    print("\n" + "-"*60)
    print(f"Results: {passed}/{total} tests passed")
    print("-"*60)
    
    if passed == total:
        print_success("\n🎉 ALL TESTS PASSED!")
        print_info("Your MT5 setup will work perfectly with Streamlit!")
        print_info("Run: streamlit run gui.py")
        return 0
    elif passed >= total - 2:
        print_warning("\n⚠️  MOSTLY WORKING")
        print_info("Minor issues detected but should work for basic operations")
        print_info("Check warnings above")
        return 0
    else:
        print_error("\n❌ SETUP ISSUES DETECTED")
        print_info("Please fix the errors above before using with Streamlit")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
