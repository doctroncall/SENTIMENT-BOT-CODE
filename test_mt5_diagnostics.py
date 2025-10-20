#!/usr/bin/env python3
"""
MT5 Connection Diagnostics Tool (with MT5 Connector Integration)
=================================================================
This script helps diagnose MT5 connection issues.
Now uses the production-grade MT5 connector when available.

Usage: python test_mt5_diagnostics.py
"""

import sys
import os
import platform

# Try to import production-grade MT5 connector
try:
    from mt5_connector import MT5Connector, MT5Config, ConnectionState
    MT5_CONNECTOR_AVAILABLE = True
except ImportError:
    MT5Connector = None
    MT5Config = None
    ConnectionState = None
    MT5_CONNECTOR_AVAILABLE = False

def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def check_platform():
    """Check if running on Windows"""
    print_section("Platform Check")
    sys_platform = platform.system()
    print(f"Operating System: {sys_platform}")
    print(f"Python Version: {sys.version}")
    
    if sys_platform != 'Windows':
        print("⚠️  WARNING: MT5 only works on Windows!")
        print("   You're running on", sys_platform)
        return False
    else:
        print("✅ Running on Windows - MT5 compatible")
        return True

def check_mt5_module():
    """Check if MT5 Python module is installed"""
    print_section("MT5 Python Module Check")
    try:
        import MetaTrader5 as mt5
        print("✅ MetaTrader5 module is installed")
        print(f"   Version: {mt5.__version__ if hasattr(mt5, '__version__') else 'Unknown'}")
        return True, mt5
    except ImportError:
        print("❌ MetaTrader5 module is NOT installed")
        print("   Install with: pip install MetaTrader5")
        return False, None

def check_mt5_terminal():
    """Check if MT5 terminal is running"""
    print_section("MT5 Terminal Check")
    
    try:
        import psutil
        terminal_processes = []
        for proc in psutil.process_iter(['name', 'exe']):
            try:
                name = proc.info['name'].lower()
                if 'terminal64.exe' in name or 'terminal.exe' in name:
                    terminal_processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if terminal_processes:
            print(f"✅ Found {len(terminal_processes)} MT5 terminal process(es) running")
            for proc in terminal_processes:
                try:
                    print(f"   - PID: {proc.pid}, Path: {proc.info.get('exe', 'Unknown')}")
                except:
                    print(f"   - PID: {proc.pid}")
            return True
        else:
            print("❌ MT5 terminal is NOT running")
            print("   Please start MetaTrader 5 and login before connecting")
            return False
            
    except ImportError:
        print("⚠️  Cannot check (psutil not installed)")
        print("   Install with: pip install psutil")
        return None

def check_mt5_path():
    """Check if MT5 terminal path exists"""
    print_section("MT5 Installation Path Check")
    
    default_path = r"C:\Program Files\MetaTrader 5\terminal64.exe"
    env_path = os.getenv("MT5_PATH")
    
    print(f"Default Path: {default_path}")
    if os.path.exists(default_path):
        print("✅ Default MT5 path exists")
    else:
        print("❌ Default MT5 path not found")
    
    if env_path:
        print(f"\nEnvironment Variable MT5_PATH: {env_path}")
        if os.path.exists(env_path):
            print("✅ Custom MT5 path exists")
        else:
            print("❌ Custom MT5 path not found")
    else:
        print("\nMT5_PATH environment variable: Not set (using default)")
    
    return os.path.exists(default_path) or (env_path and os.path.exists(env_path))

def check_credentials():
    """Check MT5 credentials configuration"""
    print_section("MT5 Credentials Check")
    
    mt5_login = os.getenv("MT5_LOGIN", "211744072")
    mt5_server = os.getenv("MT5_SERVER", "ExnessKE-MT5Trial9")
    mt5_password = os.getenv("MT5_PASSWORD")
    
    print(f"Login: {mt5_login}")
    print(f"Server: {mt5_server}")
    print(f"Password: {'Set' if mt5_password else 'Using default (check data_manager.py)'}")
    
    return True

def test_connection_with_connector():
    """Test MT5 connection using production-grade connector"""
    print_section("MT5 Connection Test (Using Production Connector)")
    
    if not MT5_CONNECTOR_AVAILABLE:
        print("⏭️  Connector not available, falling back to legacy test")
        return None
    
    try:
        print("Step 1: Creating MT5 connector instance...")
        config = MT5Config(
            login=int(os.getenv("MT5_LOGIN", "211744072")),
            password=os.getenv("MT5_PASSWORD", "dFbKaNLWQ53@9@Z"),
            server=os.getenv("MT5_SERVER", "ExnessKE-MT5Trial9"),
            path=os.getenv("MT5_PATH", r"C:\Program Files\MetaTrader 5\terminal64.exe")
        )
        
        connector = MT5Connector.get_instance(config)
        print("✅ Connector instance created")
        
        # Attempt connection
        print("\nStep 2: Connecting to MT5...")
        if connector.connect():
            print("✅ Connected successfully!")
            
            # Get account info
            print("\nStep 3: Retrieving account information...")
            account_info = connector.get_account_info()
            if account_info:
                print(f"📊 Account Information:")
                print(f"   Account: {account_info.login}")
                print(f"   Server: {account_info.server}")
                print(f"   Balance: {account_info.balance}")
                print(f"   Leverage: 1:{account_info.leverage}")
            
            # Get connection stats
            print("\nStep 4: Connection statistics...")
            stats = connector.get_connection_stats()
            print(f"   State: {stats['state']}")
            print(f"   Uptime: {stats.get('uptime_seconds', 0):.1f}s")
            print(f"   Health Check: {stats.get('last_health_check', 'N/A')}")
            
            # Test symbol retrieval
            print("\nStep 5: Testing symbol retrieval...")
            symbols = connector.get_available_symbols()
            print(f"✅ Found {len(symbols)} symbols")
            if len(symbols) > 0:
                print(f"   Sample symbols: {', '.join(symbols[:5])}")
            
            # Disconnect
            print("\nStep 6: Disconnecting...")
            connector.disconnect()
            print("✅ Disconnected successfully")
            
            print("\n✅ Connection test PASSED (via production connector)!")
            print("   Your MT5 connection is working correctly with the connector.")
            return True
        else:
            print("❌ Connection failed")
            print("\nPossible causes:")
            print("  1. MT5 terminal is not running")
            print("  2. MT5 terminal is not logged in")
            print("  3. Wrong credentials")
            print("  4. Network issues")
            return False
            
    except Exception as e:
        print(f"❌ Connector error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_connection(mt5):
    """Test actual MT5 connection (legacy method)"""
    # First try with production connector if available
    if MT5_CONNECTOR_AVAILABLE:
        result = test_connection_with_connector()
        if result is not None:
            return result
    
    # Fallback to legacy test
    print_section("MT5 Connection Test (Legacy Method)")
    
    if mt5 is None:
        print("⏭️  Skipping (MT5 module not available)")
        return False
    
    try:
        # Initialize
        print("Step 1: Initializing MT5...")
        mt5_path = os.getenv("MT5_PATH")
        if mt5_path and os.path.exists(mt5_path):
            initialized = mt5.initialize(mt5_path)
        else:
            initialized = mt5.initialize()
        
        if not initialized:
            error = mt5.last_error()
            print(f"❌ Initialization failed: {error}")
            print("\nPossible causes:")
            print("  1. MT5 terminal is not running")
            print("  2. MT5 terminal is not logged in")
            print("  3. Need to restart MT5 terminal")
            return False
        
        print("✅ MT5 initialized successfully")
        
        # Try login
        print("\nStep 2: Attempting login...")
        mt5_login = int(os.getenv("MT5_LOGIN", "211744072"))
        mt5_password = os.getenv("MT5_PASSWORD", "dFbKaNLWQ53@9@Z")
        mt5_server = os.getenv("MT5_SERVER", "ExnessKE-MT5Trial9")
        
        authorized = mt5.login(
            login=mt5_login,
            password=mt5_password,
            server=mt5_server
        )
        
        if not authorized:
            error = mt5.last_error()
            print(f"❌ Login failed: {error}")
            print("\nPossible causes:")
            print("  1. Wrong credentials")
            print("  2. Wrong server name")
            print("  3. Account not active")
            print("  4. Network issues")
            mt5.shutdown()
            return False
        
        print("✅ Login successful!")
        
        # Get account info
        account_info = mt5.account_info()
        if account_info:
            print(f"\n📊 Account Information:")
            print(f"   Account: {account_info.login}")
            print(f"   Server: {account_info.server}")
            print(f"   Balance: {account_info.balance}")
            print(f"   Leverage: 1:{account_info.leverage}")
        
        # Cleanup
        mt5.shutdown()
        print("\n✅ Connection test PASSED (legacy method)!")
        print("   Your MT5 connection is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Connection error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all diagnostic checks"""
    print("\n" + "=" * 60)
    print("  MT5 CONNECTION DIAGNOSTICS TOOL")
    print("=" * 60)
    print("\nThis tool will check your MT5 connection setup...\n")
    
    results = {}
    
    # Run checks
    results['platform'] = check_platform()
    results['module'], mt5 = check_mt5_module()
    results['terminal'] = check_mt5_terminal()
    results['path'] = check_mt5_path()
    results['credentials'] = check_credentials()
    
    # Test connection if all checks pass
    if all([results.get('platform'), results.get('module')]):
        results['connection'] = test_connection(mt5)
    else:
        print_section("MT5 Connection Test")
        print("⏭️  Skipping (prerequisites not met)")
        results['connection'] = False
    
    # Summary
    print_section("DIAGNOSTIC SUMMARY")
    print(f"Platform Compatible: {'✅' if results.get('platform') else '❌'}")
    print(f"MT5 Module Installed: {'✅' if results.get('module') else '❌'}")
    print(f"MT5 Connector Available: {'✅' if MT5_CONNECTOR_AVAILABLE else '❌'}")
    print(f"MT5 Terminal Running: {'✅' if results.get('terminal') else '⚠️ Unknown' if results.get('terminal') is None else '❌'}")
    print(f"MT5 Path Exists: {'✅' if results.get('path') else '❌'}")
    print(f"Connection Works: {'✅' if results.get('connection') else '❌'}")
    
    # Recommendations
    print("\n" + "=" * 60)
    print("  RECOMMENDATIONS")
    print("=" * 60)
    
    if not results.get('platform'):
        print("❌ MT5 only works on Windows. Use Yahoo Finance as fallback.")
    elif not results.get('module'):
        print("❌ Install MT5 module: pip install MetaTrader5")
    elif not results.get('terminal'):
        print("❌ Start MetaTrader 5 terminal and login first")
    elif not results.get('connection'):
        print("❌ Check troubleshooting guide: TROUBLESHOOT_MT5_CONNECTION.md")
        print("   Common fix: Restart MT5 terminal completely")
    else:
        print("✅ Everything looks good! Your MT5 connection should work.")
    
    print("\n" + "=" * 60)
    return 0 if results.get('connection') else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Diagnostics interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
