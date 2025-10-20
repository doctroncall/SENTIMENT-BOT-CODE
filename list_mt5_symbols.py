"""
list_mt5_symbols.py - Utility to list all available symbols in MT5
This helps identify the correct symbol names for your broker.
Now uses production-grade MT5 connector when available.
"""

import os
import sys

# Try to import production-grade MT5 connector
try:
    from mt5_connector import MT5Connector, MT5Config
    MT5_CONNECTOR_AVAILABLE = True
except ImportError:
    MT5Connector = None
    MT5Config = None
    MT5_CONNECTOR_AVAILABLE = False

# Fallback to direct MT5 module
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    mt5 = None
    MT5_AVAILABLE = False

if not MT5_CONNECTOR_AVAILABLE and not MT5_AVAILABLE:
    print("❌ Neither MT5 connector nor MetaTrader5 package is available.")
    print("   Install with: pip install MetaTrader5")
    sys.exit(1)

# Connection settings from environment or defaults
MT5_LOGIN = int(os.getenv("MT5_LOGIN", "211744072"))
MT5_PASSWORD = os.getenv("MT5_PASSWORD", "dFbKaNLWQ53@9@Z")
MT5_SERVER = os.getenv("MT5_SERVER", "ExnessKE-MT5Trial9")
MT5_PATH = os.getenv("MT5_PATH", r"C:\\Program Files\\MetaTrader 5\\terminal64.exe")


def connect_mt5_with_connector():
    """Connect to MT5 using production-grade connector"""
    try:
        config = MT5Config(
            login=MT5_LOGIN,
            password=MT5_PASSWORD,
            server=MT5_SERVER,
            path=MT5_PATH
        )
        
        connector = MT5Connector.get_instance(config)
        
        if connector.connect():
            print(f"✅ Connected to MT5 (via production connector)")
            print(f"   Login: {MT5_LOGIN}")
            print(f"   Server: {MT5_SERVER}")
            return True, connector
        else:
            print(f"❌ MT5 connection failed (via connector)")
            return False, None
            
    except Exception as e:
        print(f"❌ Error connecting with MT5 connector: {e}")
        return False, None

def connect_mt5():
    """Connect to MT5 (tries connector first, then fallback to legacy)"""
    # Try production connector first
    if MT5_CONNECTOR_AVAILABLE:
        success, connector = connect_mt5_with_connector()
        if success:
            return True, connector
        print("   Falling back to legacy connection method...")
    
    # Legacy connection method
    if not MT5_AVAILABLE:
        print("❌ MT5 module not available")
        return False, None
    
    try:
        # Initialize MT5
        if MT5_PATH and os.path.exists(MT5_PATH):
            if not mt5.initialize(MT5_PATH):
                print(f"❌ MT5 initialize failed: {mt5.last_error()}")
                return False, None
        else:
            if not mt5.initialize():
                print(f"❌ MT5 initialize failed: {mt5.last_error()}")
                return False, None
        
        # Login
        if not mt5.login(login=MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER):
            print(f"❌ MT5 login failed: {mt5.last_error()}")
            return False, None
        
        print(f"✅ Connected to MT5 (legacy method)")
        print(f"   Login: {MT5_LOGIN}")
        print(f"   Server: {MT5_SERVER}")
        return True, None
        
    except Exception as e:
        print(f"❌ Error connecting to MT5: {e}")
        return False, None


def list_all_symbols(connector=None):
    """List all available symbols"""
    # Use connector if available
    if connector is not None:
        symbol_names = connector.get_available_symbols()
        if not symbol_names:
            print("❌ No symbols found")
            return []
        
        print(f"\n{'='*80}")
        print(f"Found {len(symbol_names)} symbols (via connector)")
        print(f"{'='*80}\n")
        
        # Convert to symbol objects for compatibility
        class SymbolInfo:
            def __init__(self, name):
                self.name = name
                self.description = name
        
        return [SymbolInfo(name) for name in symbol_names]
    
    # Legacy method
    if not MT5_AVAILABLE:
        print("❌ MT5 module not available")
        return []
    
    symbols = mt5.symbols_get()
    
    if symbols is None or len(symbols) == 0:
        print("❌ No symbols found")
        return []
    
    print(f"\n{'='*80}")
    print(f"Found {len(symbols)} symbols")
    print(f"{'='*80}\n")
    
    return symbols


def find_matching_symbols(search_term, connector=None):
    """Find symbols matching a search term"""
    # Use connector if available
    if connector is not None:
        all_symbol_names = connector.get_available_symbols()
        if not all_symbol_names:
            return []
        
        search_upper = search_term.upper()
        matching_names = [s for s in all_symbol_names if search_upper in s.upper()]
        
        # Convert to symbol objects for compatibility
        class SymbolInfo:
            def __init__(self, name):
                self.name = name
                self.description = name
        
        return [SymbolInfo(name) for name in matching_names]
    
    # Legacy method
    if not MT5_AVAILABLE:
        return []
    
    symbols = mt5.symbols_get()
    
    if symbols is None:
        return []
    
    search_upper = search_term.upper()
    matching = [s for s in symbols if search_upper in s.name.upper()]
    
    return matching


def display_symbol_info(symbol_name, connector=None):
    """Display detailed information about a symbol"""
    # Use connector if available
    if connector is not None:
        symbol = connector.get_symbol_info(symbol_name)
    elif MT5_AVAILABLE:
        symbol = mt5.symbol_info(symbol_name)
    else:
        print(f"❌ Cannot get symbol info - no connection method available")
        return
    
    if symbol is None:
        print(f"❌ Symbol '{symbol_name}' not found")
        return
    
    print(f"\n{'='*60}")
    print(f"Symbol: {symbol.name}")
    print(f"{'='*60}")
    
    # Some attributes may not be available with all connection methods
    try:
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
    except AttributeError as e:
        print(f"⚠️ Some details not available: {e}")
    
    print(f"{'='*60}\n")


def main():
    """Main function"""
    print("\n" + "="*80)
    print("MT5 Symbol Lister - Find Available Symbols for Your Broker")
    if MT5_CONNECTOR_AVAILABLE:
        print("(Using Production-Grade MT5 Connector)")
    print("="*80 + "\n")
    
    # Connect to MT5
    success, connector = connect_mt5()
    if not success:
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
            matches = find_matching_symbols(search_term, connector)
            if matches:
                print(f"\n🔍 Symbols containing '{search_term}' ({len(matches)} found):")
                print("-" * 60)
                for sym in matches[:10]:  # Show first 10 matches
                    desc = getattr(sym, 'description', sym.name)
                    print(f"   • {sym.name:20s} - {desc}")
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
        # Get all symbol names
        if connector is not None:
            symbol_names = connector.get_available_symbols()
        elif MT5_AVAILABLE:
            all_symbols = mt5.symbols_get()
            symbol_names = [s.name for s in all_symbols] if all_symbols else []
        else:
            symbol_names = []
        
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
                symbols = list_all_symbols(connector)
                for sym in symbols:
                    desc = getattr(sym, 'description', sym.name)
                    print(f"{sym.name:30s} {desc}")
            
            elif sys.argv[1] == "--search" and len(sys.argv) > 2:
                search_term = sys.argv[2]
                matches = find_matching_symbols(search_term, connector)
                print(f"\n🔍 Symbols matching '{search_term}':")
                for sym in matches:
                    display_symbol_info(sym.name, connector)
        
    finally:
        # Disconnect
        if connector is not None:
            connector.disconnect()
            print("\n✅ Disconnected from MT5 (via connector)")
        elif MT5_AVAILABLE:
            mt5.shutdown()
            print("\n✅ Disconnected from MT5")


if __name__ == "__main__":
    main()
