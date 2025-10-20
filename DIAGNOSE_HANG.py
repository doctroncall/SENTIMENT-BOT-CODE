#!/usr/bin/env python3
"""
Diagnose where the MT5 connection is hanging
"""
import sys
import time
import traceback

print("=" * 70)
print("MT5 CONNECTION HANG DIAGNOSTIC")
print("=" * 70)
print()

# Test 1: Basic imports
print("Test 1: Importing modules...")
try:
    import MetaTrader5 as mt5
    print("  ✓ MetaTrader5 imported")
except Exception as e:
    print(f"  ✗ MetaTrader5 import failed: {e}")
    sys.exit(1)

try:
    from mt5_connector import MT5Connector, MT5Config
    print("  ✓ MT5Connector imported")
except Exception as e:
    print(f"  ✗ MT5Connector import failed: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    from data_manager import DataManager
    print("  ✓ DataManager imported")
except Exception as e:
    print(f"  ✗ DataManager import failed: {e}")
    traceback.print_exc()
    sys.exit(1)

print()

# Test 2: Check MT5 terminal status
print("Test 2: Checking MT5 terminal status...")
try:
    # Try to get terminal info without initializing
    info = mt5.terminal_info()
    if info:
        print(f"  ✓ MT5 terminal is running")
        print(f"    Version: {info.build}")
        print(f"    Company: {info.company}")
    else:
        print(f"  ⚠ MT5 terminal info not available (may not be running)")
except Exception as e:
    print(f"  ⚠ Could not get terminal info: {e}")

print()

# Test 3: Try direct MT5 initialization (with timeout)
print("Test 3: Testing direct MT5 initialization...")
print("  (This will timeout after 10 seconds if hanging)")
import threading

def test_init():
    try:
        result = mt5.initialize()
        print(f"  → mt5.initialize() returned: {result}")
        if result:
            mt5.shutdown()
            print(f"  ✓ Direct initialization works")
        else:
            error = mt5.last_error()
            print(f"  ✗ Initialization failed: {error}")
    except Exception as e:
        print(f"  ✗ Exception during initialization: {e}")

thread = threading.Thread(target=test_init, daemon=True)
thread.start()
thread.join(timeout=10)

if thread.is_alive():
    print("  ✗ HANG DETECTED: mt5.initialize() is hanging!")
    print("  → This means MT5 terminal might have a modal dialog open")
    print("  → Or MT5 is waiting for user input")
    print("  → Check MT5 terminal window for prompts/dialogs")
else:
    print("  ✓ mt5.initialize() completed (no hang)")

print()

# Test 4: Try MT5Connector
print("Test 4: Testing MT5Connector...")
print("  Creating config...")
config = MT5Config(
    login=211744072,
    password="dFbKaNLWQ53@9@Z",
    server="ExnessKE-MT5Trial9",
    path=r"C:\Program Files\MetaTrader 5\terminal64.exe",
    timeout=10000  # 10 second timeout
)
print(f"  Config: {config}")

def test_connector():
    try:
        print("  Getting MT5Connector instance...")
        connector = MT5Connector.get_instance(config)
        print("  Calling connector.connect()...")
        result = connector.connect()
        print(f"  → connector.connect() returned: {result}")
        if result:
            print(f"  ✓ MT5Connector works")
            connector.disconnect()
        else:
            print(f"  ✗ Connection failed")
    except Exception as e:
        print(f"  ✗ Exception in connector: {e}")
        traceback.print_exc()

thread2 = threading.Thread(target=test_connector, daemon=True)
thread2.start()
thread2.join(timeout=15)

if thread2.is_alive():
    print("  ✗ HANG DETECTED: MT5Connector.connect() is hanging!")
    print()
    print("DIAGNOSIS:")
    print("  The hang is in MT5Connector.connect()")
    print("  Most likely cause:")
    print("    - MT5 terminal has a modal dialog open")
    print("    - MT5 is prompting for update or login")
    print("    - MT5 path is incorrect")
    print()
    print("SOLUTION:")
    print("  1. Open MT5 terminal manually")
    print("  2. Close any dialogs/prompts")
    print("  3. Login to account 211744072")
    print("  4. Try again")
else:
    print("  ✓ MT5Connector completed (no hang)")

print()

# Test 5: Try DataManager
print("Test 5: Testing DataManager...")
def test_datamanager():
    try:
        print("  Creating DataManager...")
        dm = DataManager()
        print("  Calling dm.connect()...")
        result = dm.connect()
        print(f"  → dm.connect() returned: {result}")
        if result:
            print(f"  ✓ DataManager works")
            dm.disconnect()
        else:
            print(f"  ✗ Connection failed")
    except Exception as e:
        print(f"  ✗ Exception in DataManager: {e}")
        traceback.print_exc()

thread3 = threading.Thread(target=test_datamanager, daemon=True)
thread3.start()
thread3.join(timeout=15)

if thread3.is_alive():
    print("  ✗ HANG DETECTED: DataManager.connect() is hanging!")
else:
    print("  ✓ DataManager completed (no hang)")

print()
print("=" * 70)
print("DIAGNOSTIC COMPLETE")
print("=" * 70)
