# MT5 Connector Quick Start Guide

## 🚀 What's New?

A professional, production-grade MT5 connector module (`mt5_connector.py`) has been created and integrated into your trading bot. This provides:

- ✅ Reliable, automatic reconnection
- ✅ Thread-safe operations
- ✅ Health monitoring & diagnostics
- ✅ Connection pooling (singleton pattern)
- ✅ Comprehensive error handling
- ✅ Detailed logging
- ✅ Symbol caching for performance
- ✅ Backward compatibility (no breaking changes!)

## 📦 What Was Changed?

### New File
- **`mt5_connector.py`** - Professional MT5 connection manager (35KB, 900+ lines)

### Enhanced Files (100% Backward Compatible)
- **`data_manager.py`** - Now uses MT5 connector when available
- **`verifier.py`** - Enhanced with connector support
- **`test_mt5_diagnostics.py`** - Connector-aware diagnostics
- **`list_mt5_symbols.py`** - Uses connector for better performance

## ✅ Nothing Breaks!

**Your existing code continues to work exactly as before.** The connector:
- Auto-detects and uses itself if available
- Falls back to legacy MT5 module if needed
- Requires no changes to your existing scripts

## 🎯 Quick Test

### Test 1: Check Connector Availability
```bash
python3 -c "from mt5_connector import MT5Connector; print('✅ Connector available!')"
```

### Test 2: Run Diagnostics
```bash
python3 test_mt5_diagnostics.py
```

### Test 3: Test Connection
```python
from mt5_connector import MT5Connector

# Get connector
connector = MT5Connector.get_instance()

# Connect
if connector.connect():
    print("✅ Connected!")
    
    # Get stats
    stats = connector.get_connection_stats()
    print(f"Uptime: {stats['uptime_seconds']:.1f}s")
    
    # Get symbols
    symbols = connector.get_available_symbols()
    print(f"Found {len(symbols)} symbols")
    
    # Disconnect
    connector.disconnect()
else:
    print("❌ Connection failed")
```

## 💡 How to Use

### Option 1: No Changes (Automatic)
Your existing code automatically uses the connector:

```python
from data_manager import DataManager

dm = DataManager()
dm.connect()  # Now uses MT5 connector if available!
```

### Option 2: Direct Usage (Recommended for New Code)
```python
from mt5_connector import MT5Connector, mt5_connection

# Method 1: Manual
connector = MT5Connector.get_instance()
if connector.connect():
    symbols = connector.get_available_symbols()
    connector.disconnect()

# Method 2: Context Manager (Best Practice)
with mt5_connection() as connector:
    if connector.is_connected():
        symbols = connector.get_available_symbols()
```

## 🔧 Configuration

### Via Environment Variables (Recommended)
```bash
export MT5_LOGIN=12345678
export MT5_PASSWORD="your_password"
export MT5_SERVER="YourBroker-Server"
export MT5_PATH="C:\Program Files\MetaTrader 5\terminal64.exe"
export MT5_TIMEOUT_MS=30000
export MT5_MAX_RETRIES=3
```

### Via Python Code
```python
from mt5_connector import MT5Config, MT5Connector

config = MT5Config(
    login=12345678,
    password="your_password",
    server="YourBroker-Server",
    timeout=30000,
    max_retries=5
)

connector = MT5Connector.get_instance(config)
```

## 📊 Key Features

### 1. Automatic Reconnection
```python
connector.connect()  # Retries with exponential backoff
```

### 2. Health Monitoring
```python
# Automatic health checks every 5 minutes (configurable)
# Auto-reconnects if connection fails
```

### 3. Connection Stats
```python
stats = connector.get_connection_stats()
print(stats)
# {
#     'state': 'connected',
#     'uptime_seconds': 3600.5,
#     'connection_attempts': 1,
#     'cached_symbols': 150,
#     ...
# }
```

### 4. Symbol Caching
```python
# First call: queries MT5
symbol = connector.find_symbol("GBPUSD")

# Second call: uses cache (instant!)
symbol = connector.find_symbol("GBPUSD")
```

### 5. Comprehensive Logging
```bash
# Logs automatically saved to:
logs/mt5_connector_YYYYMMDD.log
logs/mt5_connection_YYYYMMDD_HHMMSS.log
```

## 🎨 Advanced Usage

### Custom Timeouts
```python
config = MT5Config(
    timeout=60000,  # 60 seconds
    max_retries=10,
    retry_delay=3.0  # 3 seconds between retries
)
```

### Force Reconnection
```python
connector.connect(force_reconnect=True)
```

### Check Connection Health
```python
if connector.health_check():
    print("✅ Connection healthy")
else:
    print("⚠️ Connection issues detected")
```

### Get Account Information
```python
account = connector.get_account_info()
print(f"Balance: {account.balance}")
print(f"Leverage: 1:{account.leverage}")
```

## 🐛 Troubleshooting

### Check Logs
```bash
cat logs/mt5_connector_*.log
```

### Run Diagnostics
```bash
python3 test_mt5_diagnostics.py
```

### Check Connection Status
```python
connector = MT5Connector.get_instance()
print(f"Connected: {connector.is_connected()}")
print(f"State: {connector.get_state()}")
```

### View Connection Stats
```python
import json
stats = connector.get_connection_stats()
print(json.dumps(stats, indent=2))
```

## 📚 Documentation

For complete documentation, see:
- **`MT5_CONNECTOR_INTEGRATION_SUMMARY.md`** - Full integration details
- **`mt5_connector.py`** - Source code with extensive docstrings

## 🎓 Examples

### Example 1: Simple Connection Test
```python
from mt5_connector import MT5Connector

connector = MT5Connector.get_instance()

if connector.connect():
    print("✅ Connected successfully!")
    account = connector.get_account_info()
    print(f"Account: {account.login}")
    print(f"Server: {account.server}")
    connector.disconnect()
```

### Example 2: Fetch Historical Data
```python
from mt5_connector import MT5Connector
import MetaTrader5 as mt5
from datetime import datetime

connector = MT5Connector.get_instance()
connector.connect()

rates = connector.get_rates(
    symbol="GBPUSD",
    timeframe=mt5.TIMEFRAME_D1,
    date_from=int(datetime(2024, 1, 1).timestamp()),
    date_to=int(datetime(2024, 2, 1).timestamp())
)

print(f"Fetched {len(rates)} candles")
```

### Example 3: Symbol Search
```python
from mt5_connector import MT5Connector

connector = MT5Connector.get_instance()
connector.connect()

# Find exact symbol
symbol = connector.find_symbol("GBPUSD")
print(f"Found: {symbol}")

# Get symbol info
info = connector.get_symbol_info(symbol)
print(f"Spread: {info.spread}")
print(f"Digits: {info.digits}")
```

## 🔐 Best Practices

1. **Use Context Managers**
   ```python
   with mt5_connection() as connector:
       # Your code here
   ```

2. **Check Connection Before Operations**
   ```python
   if connector.is_connected():
       # Safe to use
   ```

3. **Handle Exceptions**
   ```python
   try:
       connector.connect()
   except MT5ConnectionError as e:
       print(f"Connection failed: {e}")
   ```

4. **Monitor Logs**
   - Check `logs/` directory regularly
   - Look for errors and warnings

5. **Use Environment Variables**
   - Never hardcode credentials
   - Use `.env` files or system environment

## 🚦 Status Indicators

The connector provides clear status indicators:

- ✅ **CONNECTED** - Working normally
- 🔄 **CONNECTING** - Attempting connection
- 🔁 **RECONNECTING** - Auto-recovery in progress
- ⚠️ **ERROR** - Connection failed
- ⏸️ **DISCONNECTED** - Not connected

## 🎯 Summary

**What You Need to Know:**
1. ✅ Your code works as-is (backward compatible)
2. 📈 Better reliability and performance
3. 🔧 More configuration options
4. 📊 Better monitoring and diagnostics
5. 🚀 Production-ready code

**What You Can Do Now:**
1. Test the connector with diagnostics
2. Review logs for detailed information
3. Use connector directly in new code
4. Customize configuration as needed

## 📞 Need Help?

1. Check logs: `logs/mt5_connector_*.log`
2. Run diagnostics: `python3 test_mt5_diagnostics.py`
3. Read full docs: `MT5_CONNECTOR_INTEGRATION_SUMMARY.md`
4. Check connector stats: `connector.get_connection_stats()`

---

**Status**: ✅ Integrated and Ready  
**Compatibility**: 100% Backward Compatible  
**Quality**: Production-Grade
