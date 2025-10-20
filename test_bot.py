#!/usr/bin/env python3
"""
test_bot.py - Comprehensive Trading Bot Testing Suite

Runs all tests to verify the bot is working correctly.
"""

import sys
import traceback
from datetime import datetime

def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")

def print_test(name, passed, details=""):
    """Print test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {name}")
    if details:
        for line in details.split('\n'):
            print(f"       {line}")
    print()

def test_imports():
    """Test if all required modules can be imported"""
    print_header("TEST 1: Module Imports")
    
    modules = [
        ('data_manager', 'DataManager'),
        ('structure_analyzer', 'StructureAnalyzer'),
        ('sentiment_engine', 'SentimentEngine'),
        ('dashboard', 'Dashboard'),
    ]
    
    all_passed = True
    for module_name, class_name in modules:
        try:
            module = __import__(module_name)
            cls = getattr(module, class_name)
            print_test(f"Import {module_name}.{class_name}", True)
        except Exception as e:
            print_test(f"Import {module_name}.{class_name}", False, str(e))
            all_passed = False
    
    return all_passed

def test_mt5_connection():
    """Test MT5 connection"""
    print_header("TEST 2: MT5 Connection")
    
    try:
        from data_manager import DataManager
        
        dm = DataManager()
        
        if dm.connect():
            details = f"Server: {dm.mt5_server}\nLogin: {dm.mt5_login}"
            print_test("MT5 Connection", True, details)
            dm.disconnect()
            return True
        else:
            print_test("MT5 Connection", False, "Could not connect - check credentials")
            return False
            
    except Exception as e:
        print_test("MT5 Connection", False, str(e))
        return False

def test_data_fetching():
    """Test data fetching"""
    print_header("TEST 3: Data Fetching")
    
    try:
        from data_manager import DataManager
        
        dm = DataManager()
        dm.connect()
        
        # Test single timeframe
        df = dm.fetch_ohlcv_for_timeframe('GBPUSD', 'H1', lookback_days=7)
        
        if not df.empty:
            details = (f"Fetched: {len(df)} bars\n"
                      f"Columns: {list(df.columns)}\n"
                      f"Date range: {df.index.min()} to {df.index.max()}")
            print_test("Data Fetching (H1)", True, details)
            
            # Test multi-timeframe
            data = dm.get_symbol_data('GBPUSD', timeframes=['D1', 'H4', 'H1'], lookback_days=30)
            
            if data and len(data) > 0:
                details = "\n".join([f"{tf}: {len(df)} bars" for tf, df in data.items()])
                print_test("Multi-Timeframe Fetching", True, details)
                dm.disconnect()
                return True
            else:
                print_test("Multi-Timeframe Fetching", False, "No data returned")
                dm.disconnect()
                return False
        else:
            print_test("Data Fetching", False, "Empty DataFrame returned")
            dm.disconnect()
            return False
            
    except Exception as e:
        print_test("Data Fetching", False, str(e))
        traceback.print_exc()
        return False

def test_smc_analysis():
    """Test SMC analysis"""
    print_header("TEST 4: SMC Analysis")
    
    try:
        from data_manager import DataManager
        from structure_analyzer import StructureAnalyzer
        
        dm = DataManager()
        dm.connect()
        
        df = dm.fetch_ohlcv_for_timeframe('GBPUSD', 'H4', lookback_days=60)
        
        if df.empty:
            print_test("SMC Analysis", False, "No data for analysis")
            dm.disconnect()
            return False
        
        analyzer = StructureAnalyzer(df)
        
        # Test each component
        tests_passed = 0
        
        try:
            swing_highs, swing_lows = analyzer.detect_structure()
            print_test("Market Structure", True, 
                      f"Swings: {len(swing_highs)} highs, {len(swing_lows)} lows")
            tests_passed += 1
        except Exception as e:
            print_test("Market Structure", False, str(e))
        
        try:
            bos = analyzer.detect_bos()
            print_test("BOS Detection", True, f"Found: {len(bos)} BOS points")
            tests_passed += 1
        except Exception as e:
            print_test("BOS Detection", False, str(e))
        
        try:
            fvgs = analyzer.detect_fair_value_gaps()
            print_test("Fair Value Gaps", True, f"Found: {len(fvgs)} FVGs")
            tests_passed += 1
        except Exception as e:
            print_test("Fair Value Gaps", False, str(e))
        
        try:
            obs = analyzer.detect_order_blocks()
            print_test("Order Blocks", True, f"Found: {len(obs)} order blocks")
            tests_passed += 1
        except Exception as e:
            print_test("Order Blocks", False, str(e))
        
        try:
            liquidity = analyzer.detect_liquidity_zones()
            print_test("Liquidity Zones", True, f"Found: {len(liquidity)} zones")
            tests_passed += 1
        except Exception as e:
            print_test("Liquidity Zones", False, str(e))
        
        dm.disconnect()
        return tests_passed >= 3  # At least 3 out of 5 should pass
        
    except Exception as e:
        print_test("SMC Analysis", False, str(e))
        traceback.print_exc()
        return False

def test_sentiment_engine():
    """Test sentiment analysis"""
    print_header("TEST 5: Sentiment Analysis")
    
    try:
        from data_manager import DataManager
        from sentiment_engine import SentimentEngine
        
        dm = DataManager()
        dm.connect()
        
        data = dm.get_symbol_data('GBPUSD', timeframes=['D1', 'H4', 'H1'], lookback_days=60)
        
        if not data:
            print_test("Sentiment Analysis", False, "No data for analysis")
            dm.disconnect()
            return False
        
        engine = SentimentEngine(data)
        sentiment = engine.compute_sentiment()
        
        details = (f"Score: {sentiment.get('score', 0):.2f}\n"
                  f"Direction: {sentiment.get('direction', 'N/A')}\n"
                  f"Confidence: {sentiment.get('confidence', 0):.1%}")
        
        print_test("Sentiment Analysis", True, details)
        
        dm.disconnect()
        return True
        
    except Exception as e:
        print_test("Sentiment Analysis", False, str(e))
        traceback.print_exc()
        return False

def test_multi_symbol():
    """Test with multiple symbols"""
    print_header("TEST 6: Multiple Symbols")
    
    try:
        from data_manager import DataManager
        
        symbols = ['GBPUSD', 'XAUUSD', 'EURUSD']
        dm = DataManager()
        dm.connect()
        
        results = []
        for symbol in symbols:
            try:
                df = dm.fetch_ohlcv_for_timeframe(symbol, 'H1', lookback_days=2)
                if not df.empty:
                    results.append(f"✓ {symbol}: {len(df)} bars")
                else:
                    results.append(f"✗ {symbol}: No data")
            except Exception as e:
                results.append(f"✗ {symbol}: {str(e)[:30]}")
        
        details = "\n".join(results)
        success = all('✓' in r for r in results)
        
        print_test("Multiple Symbols", success, details)
        
        dm.disconnect()
        return success
        
    except Exception as e:
        print_test("Multiple Symbols", False, str(e))
        return False

def main():
    """Run all tests"""
    print("\n")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║                                                                    ║")
    print("║              TRADING BOT - COMPREHENSIVE TEST SUITE                ║")
    print("║                                                                    ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print(f"\nTest started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Run tests
    results['Imports'] = test_imports()
    results['MT5 Connection'] = test_mt5_connection()
    
    if results['MT5 Connection']:
        results['Data Fetching'] = test_data_fetching()
        results['SMC Analysis'] = test_smc_analysis()
        results['Sentiment Engine'] = test_sentiment_engine()
        results['Multi-Symbol'] = test_multi_symbol()
    else:
        print("\n⚠️  Skipping further tests due to connection failure")
        print("   Run: python fix_symbols.py")
    
    # Summary
    print_header("TEST SUMMARY")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print()
    print("─" * 70)
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print("─" * 70)
    print()
    
    if passed == total:
        print("🎉 SUCCESS! All tests passed!")
        print()
        print("Your trading bot is ready to use:")
        print("  • Run analysis: python -m dashboard")
        print("  • Launch GUI: streamlit run gui.py")
        print()
        return 0
    elif passed >= total * 0.7:
        print("⚠️  PARTIAL SUCCESS: Most tests passed")
        print()
        print("Some components may need attention.")
        print("Check the failed tests above.")
        print()
        return 1
    else:
        print("❌ FAILED: Multiple tests failed")
        print()
        print("Troubleshooting:")
        print("  1. Run: python fix_symbols.py")
        print("  2. Check MT5 connection")
        print("  3. Verify credentials in data_manager.py")
        print()
        return 2

if __name__ == "__main__":
    sys.exit(main())
