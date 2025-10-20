"""
fix_symbols.py - Quick utility to fix symbol naming issues

This script will:
1. Connect to your MT5 broker
2. List all available symbols
3. Auto-discover correct symbol names for common pairs
4. Update your configuration
"""

import os
import json
from data_manager import DataManager

def main():
    print("\n" + "="*80)
    print("🔧 SYMBOL FIXER - Auto-discover correct symbol names")
    print("="*80 + "\n")
    
    # Initialize DataManager
    dm = DataManager()
    
    # Try to connect
    print("Connecting to MT5...")
    if not dm.connect():
        print("❌ Failed to connect to MT5")
        print("   Please check your credentials in data_manager.py")
        return
    
    print("✅ Connected to MT5 successfully!\n")
    
    # Test common symbols
    test_symbols = ["GBPUSD", "XAUUSD", "EURUSD", "USDJPY", "BTCUSD"]
    
    print("="*80)
    print("SEARCHING FOR SYMBOLS")
    print("="*80 + "\n")
    
    found_mapping = {}
    not_found = []
    
    for symbol in test_symbols:
        print(f"🔍 Searching for {symbol}...")
        broker_symbol = dm.find_broker_symbol(symbol)
        
        if broker_symbol:
            found_mapping[symbol] = broker_symbol
            if broker_symbol == symbol:
                print(f"   ✅ Found: {symbol} (exact match)")
            else:
                print(f"   ✅ Found: {symbol} -> {broker_symbol}")
        else:
            not_found.append(symbol)
            print(f"   ❌ Not found: {symbol}")
        print()
    
    # Summary
    print("="*80)
    print("SUMMARY")
    print("="*80 + "\n")
    
    if found_mapping:
        print(f"✅ Found {len(found_mapping)} symbols:\n")
        for standard, broker in found_mapping.items():
            print(f"   {standard:10s} -> {broker}")
        
        # Save to config
        config_dir = "config"
        os.makedirs(config_dir, exist_ok=True)
        
        config_file = os.path.join(config_dir, "symbol_mapping.json")
        with open(config_file, 'w') as f:
            json.dump(found_mapping, f, indent=4)
        
        print(f"\n💾 Saved symbol mapping to: {config_file}")
    
    if not_found:
        print(f"\n❌ Could not find {len(not_found)} symbols:")
        for symbol in not_found:
            print(f"   • {symbol}")
        
        print("\n💡 TIP: Run 'python list_mt5_symbols.py' to see all available symbols")
        print("        You can then manually add the correct names to SYMBOL_VARIATIONS")
    
    # Test fetching data
    if found_mapping:
        print("\n" + "="*80)
        print("TESTING DATA FETCH")
        print("="*80 + "\n")
        
        # Test first found symbol
        test_symbol = list(found_mapping.keys())[0]
        print(f"Testing data fetch for {test_symbol}...")
        
        try:
            df = dm.fetch_ohlcv_for_timeframe(
                test_symbol,
                "H1",
                lookback_days=7,
                use_yahoo_fallback=False
            )
            
            if not df.empty:
                print(f"✅ Successfully fetched {len(df)} bars!")
                print(f"   Date range: {df.index.min()} to {df.index.max()}")
                print(f"   Last close: {df['close'].iloc[-1]:.5f}")
                print("\n🎉 Your MT5 connection is working correctly!")
            else:
                print("⚠️ Connected but no data returned")
        except Exception as e:
            print(f"❌ Error fetching data: {e}")
    
    # Cleanup
    dm.disconnect()
    
    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("\n1. If symbols were found, you can now run your analysis")
    print("2. The system will automatically use the correct broker-specific names")
    print("3. Run the GUI again and it should work!")
    print("\n   Example: streamlit run gui.py")
    print("\n")


if __name__ == "__main__":
    main()
