"""
list_mt5_symbols.py - Utility to list all available symbols in MT5
This helps identify the correct symbol names for your broker.
"""

import os
import sys

try:
    import MetaTrader5 as mt5
except ImportError:
    print("❌ MetaTrader5 package not installed. Run: pip install MetaTrader5")
    sys.exit(1)

# Connection settings from environment or defaults
MT5_LOGIN = int(os.getenv("MT5_LOGIN", "211744072"))
MT5_PASSWORD = os.getenv("MT5_PASSWORD", "dFbKaNLWQ53@9@Z")
MT5_SERVER = os.getenv("MT5_SERVER", "ExnessKE-MT5Trial9")
MT5_PATH = os.getenv("MT5_PATH", r"C:\\Program Files\\MetaTrader 5\\terminal64.exe")


def connect_mt5():
    """Connect to MT5"""
    try:
        # Initialize MT5
        if MT5_PATH and os.path.exists(MT5_PATH):
            if not mt5.initialize(MT5_PATH):
                print(f"❌ MT5 initialize failed: {mt5.last_error()}")
                return False
        else:
            if not mt5.initialize():
                print(f"❌ MT5 initialize failed: {mt5.last_error()}")
                return False
        
        # Login
        if not mt5.login(login=MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER):
            print(f"❌ MT5 login failed: {mt5.last_error()}")
            return False
        
        print(f"✅ Connected to MT5")
        print(f"   Login: {MT5_LOGIN}")
        print(f"   Server: {MT5_SERVER}")
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to MT5: {e}")
        return False


def list_all_symbols():
    """List all available symbols"""
    symbols = mt5.symbols_get()
    
    if symbols is None or len(symbols) == 0:
        print("❌ No symbols found")
        return []
    
    print(f"\n{'='*80}")
    print(f"Found {len(symbols)} symbols")
    print(f"{'='*80}\n")
    
    return symbols


def find_matching_symbols(search_term):
    """Find symbols matching a search term"""
    symbols = mt5.symbols_get()
    
    if symbols is None:
        return []
    
    search_upper = search_term.upper()
    matching = [s for s in symbols if search_upper in s.name.upper()]
    
    return matching


def display_symbol_info(symbol_name):
    """Display detailed information about a symbol"""
    symbol = mt5.symbol_info(symbol_name)
    
    if symbol is None:
        print(f"❌ Symbol '{symbol_name}' not found")
        return
    
    print(f"\n{'='*60}")
    print(f"Symbol: {symbol.name}")
    print(f"{'='*60}")
    print(f"Description: {symbol.description}")
    print(f"Path: {symbol.path}")
    print(f"Currency Base: {symbol.currency_base}")
    print(f"Currency Profit: {symbol.currency_profit}")
    print(f"Currency Margin: {symbol.currency_margin}")
    print(f"Digits: {symbol.digits}")
    print(f"Trade Mode: {symbol.trade_mode}")
    print(f"Point: {symbol.point}")
    print(f"Spread: {symbol.spread}")
    print(f"Visible: {symbol.visible}")
    print(f"{'='*60}\n")


def main():
    """Main function"""
    print("\n" + "="*80)
    print("MT5 Symbol Lister - Find Available Symbols for Your Broker")
    print("="*80 + "\n")
    
    # Connect to MT5
    if not connect_mt5():
        print("\n❌ Failed to connect to MT5. Please check your credentials.")
        sys.exit(1)
    
    try:
        # Search for common forex pairs
        common_searches = ["GBP", "USD", "EUR", "XAU", "GOLD", "BTCUSD"]
        
        print("\n" + "="*80)
        print("SEARCHING FOR COMMON TRADING SYMBOLS")
        print("="*80 + "\n")
        
        found_symbols = {}
        
        for search_term in common_searches:
            matches = find_matching_symbols(search_term)
            if matches:
                print(f"\n🔍 Symbols containing '{search_term}' ({len(matches)} found):")
                print("-" * 60)
                for sym in matches[:10]:  # Show first 10 matches
                    print(f"   • {sym.name:20s} - {sym.description}")
                    found_symbols[sym.name] = sym
                
                if len(matches) > 10:
                    print(f"   ... and {len(matches) - 10} more")
        
        # Create suggested mapping
        print("\n" + "="*80)
        print("SUGGESTED SYMBOL MAPPING FOR YOUR CONFIGURATION")
        print("="*80 + "\n")
        
        # Common pairs to look for
        desired_pairs = {
            "GBPUSD": ["GBPUSD", "GBPUSDm", "GBPUSD.a", "GBPUSD."],
            "XAUUSD": ["XAUUSD", "XAUUSDm", "GOLD", "GOLDm", "XAUUSD."],
            "EURUSD": ["EURUSD", "EURUSDm", "EURUSD.a", "EURUSD."],
            "USDJPY": ["USDJPY", "USDJPYm", "USDJPY.a"],
            "BTCUSD": ["BTCUSD", "BTCUSDm", "BTCUSD."],
        }
        
        mapping = {}
        all_symbols = mt5.symbols_get()
        symbol_names = [s.name for s in all_symbols] if all_symbols else []
        
        for standard_name, variations in desired_pairs.items():
            for variant in variations:
                if variant in symbol_names:
                    mapping[standard_name] = variant
                    print(f"✅ {standard_name:10s} -> {variant}")
                    break
            else:
                print(f"❌ {standard_name:10s} -> NOT FOUND (searched: {', '.join(variations)})")
        
        # Generate configuration code
        if mapping:
            print("\n" + "="*80)
            print("PYTHON CODE TO ADD TO YOUR CONFIGURATION")
            print("="*80 + "\n")
            print("# Add this to data_manager.py or create a config file:")
            print("\nBROKER_SYMBOL_MAPPING = {")
            for standard, broker_specific in mapping.items():
                print(f'    "{standard}": "{broker_specific}",')
            print("}\n")
        
        # Show how to list all symbols
        print("\n" + "="*80)
        print("NEED TO SEE ALL SYMBOLS?")
        print("="*80)
        print("\nTo see all available symbols, run:")
        print("  python list_mt5_symbols.py --all")
        print("\nTo search for specific symbols, run:")
        print("  python list_mt5_symbols.py --search GBPUSD")
        
        # Check command line arguments
        if len(sys.argv) > 1:
            if sys.argv[1] == "--all":
                print("\n" + "="*80)
                print("ALL AVAILABLE SYMBOLS")
                print("="*80 + "\n")
                symbols = list_all_symbols()
                for sym in symbols:
                    print(f"{sym.name:30s} {sym.description}")
            
            elif sys.argv[1] == "--search" and len(sys.argv) > 2:
                search_term = sys.argv[2]
                matches = find_matching_symbols(search_term)
                print(f"\n🔍 Symbols matching '{search_term}':")
                for sym in matches:
                    display_symbol_info(sym.name)
        
    finally:
        mt5.shutdown()
        print("\n✅ Disconnected from MT5")


if __name__ == "__main__":
    main()
