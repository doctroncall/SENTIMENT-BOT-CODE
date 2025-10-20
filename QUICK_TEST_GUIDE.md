# Quick Test Guide - MT5 Bot Fixes

## 🚀 Quick Start

### 1. Test Symbol Normalization
```bash
cd /workspace
python symbol_utils.py
```

**Expected Output:**
```
Testing symbol normalization:
==================================================
✓ "GBP/USD"          → "GBPUSD"   (expected "GBPUSD")
✓ "GBP USD"          → "GBPUSD"   (expected "GBPUSD")
✓ "gbpusd"           → "GBPUSD"   (expected "GBPUSD")
✓ "xau/usd"          → "XAUUSD"   (expected "XAUUSD")
✓ " EUR_USD "        → "EURUSD"   (expected "EURUSD")
✓ "BTCUSD"           → "BTCUSD"   (expected "BTCUSD")
✓ ""                 → ""         (expected "")
==================================================
✅ All tests passed!
```

---

### 2. Test MT5 Connection
```bash
cd /workspace
python -c "
from mt5_connector import MT5Connector, MT5Config

config = MT5Config(
    login=211744072,
    password='dFbKaNLWQ53@9@Z',
    server='ExnessKE-MT5Trial9',
    path=r'C:\Program Files\MetaTrader 5\terminal64.exe'
)

connector = MT5Connector.get_instance(config)
print('Connecting...')
result = connector.connect()
print(f'Connected: {result}')
print(f'State: {connector.get_state()}')
"
```

**Expected Output:**
```
Connecting...
Connected: True
State: ConnectionState.CONNECTED
```

---

### 3. Test DataManager Integration
```bash
cd /workspace
python -c "
from data_manager import DataManager

dm = DataManager()
print('Connecting via DataManager...')
result = dm.connect()
print(f'Connected: {result}')
print(f'Is connected: {dm.is_connected()}')
"
```

**Expected Output:**
```
Connecting via DataManager...
Connected: True
Is connected: True
```

---

### 4. Test Singleton Behavior
```bash
cd /workspace
python -c "
from data_manager import DataManager

dm1 = DataManager()
dm2 = DataManager()
print(f'Same connector instance: {dm1._mt5_connector is dm2._mt5_connector}')
print(f'Both show connected: {dm1.is_connected() == dm2.is_connected()}')
"
```

**Expected Output:**
```
Same connector instance: True
Both show connected: True
```

---

### 5. Run Full Bot Test Suite
```bash
cd /workspace
python test_bot.py
```

**Expected Output:**
```
╔════════════════════════════════════════════════════════════════════╗
║              TRADING BOT - COMPREHENSIVE TEST SUITE                ║
╚════════════════════════════════════════════════════════════════════╝

Test started: 2025-10-20 XX:XX:XX

======================================================================
  TEST 1: Module Imports
======================================================================

✅ PASS: Import data_manager.DataManager
✅ PASS: Import structure_analyzer.StructureAnalyzer
✅ PASS: Import sentiment_engine.SentimentEngine
✅ PASS: Import dashboard.Dashboard

======================================================================
  TEST 2: MT5 Connection
======================================================================

✅ PASS: MT5 Connection
       Server: ExnessKE-MT5Trial9
       Login: 211744072

======================================================================
  TEST 3: Data Fetching
======================================================================

✅ PASS: Data Fetching (H1)
       Fetched: XXX bars
       Columns: ['open', 'high', 'low', 'close', 'tick_volume']
       Date range: YYYY-MM-DD to YYYY-MM-DD

✅ PASS: Multi-Timeframe Fetching
       D1: XXX bars
       H4: XXX bars
       H1: XXX bars

======================================================================
  TEST 4: SMC Analysis
======================================================================

✅ PASS: Market Structure
       Swings: XX highs, XX lows
✅ PASS: BOS Detection
       Found: XX BOS points
✅ PASS: Fair Value Gaps
       Found: XX FVGs
✅ PASS: Order Blocks
       Found: XX order blocks
✅ PASS: Liquidity Zones
       Found: XX zones

======================================================================
  TEST 5: Sentiment Analysis
======================================================================

✅ PASS: Sentiment Analysis
       Score: X.XX
       Direction: BULLISH/BEARISH
       Confidence: XX.X%

======================================================================
  TEST 6: Multiple Symbols
======================================================================

✅ PASS: Multiple Symbols
       ✓ GBPUSD: XXX bars
       ✓ XAUUSD: XXX bars
       ✓ EURUSD: XXX bars

======================================================================
  TEST SUMMARY
======================================================================

✅ PASS: Imports
✅ PASS: MT5 Connection
✅ PASS: Data Fetching
✅ PASS: SMC Analysis
✅ PASS: Sentiment Engine
✅ PASS: Multi-Symbol

──────────────────────────────────────────────────────────────────────
Results: 6/6 tests passed (100%)
──────────────────────────────────────────────────────────────────────

🎉 SUCCESS! All tests passed!

Your trading bot is ready to use:
  • Run analysis: python -m dashboard
  • Launch GUI: streamlit run gui.py
```

---

## 🔍 Troubleshooting

### Issue: "MT5Connector not available"
**Solution:**
```bash
# Check if mt5_connector.py exists
ls -la mt5_connector.py

# Verify imports
python -c "from mt5_connector import MT5Connector; print('OK')"
```

### Issue: "MetaTrader5 module not found"
**Solution:**
```bash
pip install MetaTrader5
```

### Issue: "Connection failed"
**Check:**
1. MT5 terminal is running
2. Logged into correct account (211744072)
3. Server is "ExnessKE-MT5Trial9"
4. No modal dialogs open in MT5

### Issue: "Symbol not found"
**Solution:**
```bash
# List available symbols
python list_mt5_symbols.py

# Test symbol normalization
python -c "from symbol_utils import normalize_symbol; print(normalize_symbol('GBP/USD'))"
```

### Issue: "State mismatch warning"
**This is normal!** The validation system will auto-sync the states.

**Log example:**
```
WARNING - Connection state mismatch detected! 
DataManager._connected=False, MT5Connector.is_connected()=True. 
Syncing to connector state.
```

**Action:** None needed - auto-synced

---

## 📊 Log Files

Check these logs for detailed information:

```bash
# Connection logs
tail -f logs/mt5_connection_*.log

# Data manager logs  
tail -f logs/data_manager_*.log

# MT5 connector logs
tail -f logs/mt5_connector_*.log
```

---

## ✅ Success Indicators

### Logs Show:
```
✅ MT5Connector initialized with config
✅ Successfully connected to MT5
✅ Connection state: connected
✅ Account: 211744072
✅ Server: ExnessKE-MT5Trial9
```

### No Errors:
```
❌ Connection state mismatch (should auto-sync)
❌ Symbol not found (check symbol_utils)
❌ Dual initialization (fixed!)
❌ Config mismatch warning (working as intended)
```

---

## 🎯 Performance Metrics

After fixes, you should see:

### Connection Speed
- First connection: ~2-5 seconds
- Subsequent (cached): < 0.1 seconds

### Symbol Lookup
- Cached symbols: instant
- New symbols: ~0.5 seconds

### Data Fetching
- H1 (30 days): ~1-3 seconds
- D1 (90 days): ~2-5 seconds

---

## 📞 Support

If tests fail:

1. **Check logs** in `logs/` directory
2. **Review** `CODEBASE_ANALYSIS_REPORT.md`
3. **Verify** all fixes in `FIXES_APPLIED_SUMMARY.md`
4. **Test individually** using commands above

---

## 🔄 Next Steps After Successful Tests

1. **Run dashboard:** `python -m dashboard`
2. **Launch GUI:** `streamlit run gui.py`
3. **Test verification:** `python verifier.py`
4. **Monitor performance:** Check logs regularly

---

**Note:** Ensure MT5 terminal is running and logged in before running tests!
