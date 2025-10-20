# Symbol Naming Issue - Fix Guide

## Problem
Your MT5 broker (Exness) uses different symbol names than the standard naming convention. For example:
- Standard: `GBPUSD`
- Exness might use: `GBPUSDm`, `GBPUSD.`, or other variations

## Quick Fix

### Option 1: Automatic Discovery (Recommended)
Run the symbol fixer script:
```bash
python fix_symbols.py
```

This will:
1. Connect to your MT5 broker
2. Auto-discover the correct symbol names
3. Test data fetching
4. Show you what symbols are available

### Option 2: List All Available Symbols
To see ALL symbols available in your MT5:
```bash
python list_mt5_symbols.py --all
```

To search for specific symbols:
```bash
python list_mt5_symbols.py --search GBPUSD
```

### Option 3: Manual Configuration
If you know the correct symbol names, you can manually add them to `data_manager.py`:

```python
# Add to SYMBOL_VARIATIONS in data_manager.py
SYMBOL_VARIATIONS = {
    "GBPUSD": ["GBPUSD", "GBPUSDm", "GBPUSD.a", "GBPUSD."],  # Add your broker's variation
    "XAUUSD": ["XAUUSD", "XAUUSDm", "GOLD", "GOLDm"],
    # ... etc
}
```

## Understanding the Error

From your logs:
```
MT5 fetch failed for GBPUSD D1: Symbol GBPUSD not found in MT5
```

This means:
- ✅ MT5 connection is working
- ✅ You're logged in successfully
- ❌ The symbol name "GBPUSD" doesn't exist in your broker's symbol list
- 💡 Your broker uses a different name (like "GBPUSDm")

## How the Fix Works

The updated `data_manager.py` now:

1. **Auto-discovers** broker-specific symbol names
2. **Caches** the mappings so it doesn't search repeatedly
3. **Tries variations** like "GBPUSDm", "GBPUSD.", etc.
4. **Fuzzy searches** if exact matches aren't found
5. **Logs helpful info** about what's available

## After Fixing

Once symbols are correctly mapped:
1. Restart your GUI: `streamlit run gui.py`
2. Try fetching data again
3. The system will automatically use the correct broker-specific names

## Common Broker Naming Conventions

| Broker | Naming Pattern | Example |
|--------|---------------|---------|
| Exness | Adds 'm' suffix | GBPUSDm |
| IC Markets | Standard | GBPUSD |
| Pepperstone | Standard or '.a' | GBPUSD or GBPUSD.a |
| FXCM | Standard | GBPUSD |
| Oanda | Different format | GBP_USD |

## Testing the Fix

After running the fix, test it:
```python
from data_manager import DataManager

dm = DataManager()
dm.connect()

# This should now work
df = dm.fetch_ohlcv_for_timeframe("GBPUSD", "H1", lookback_days=7)
print(f"Fetched {len(df)} bars")

dm.disconnect()
```

## Still Not Working?

If you're still having issues:

1. **Check your MT5 symbols manually:**
   - Open MT5 Terminal
   - Go to "Market Watch" (Ctrl+M)
   - Right-click → "Symbols"
   - Search for your desired currency pair
   - Note the EXACT name shown

2. **Verify MT5 connection:**
   ```bash
   python list_mt5_symbols.py
   ```
   This will show if you're connected and what symbols are available

3. **Check logs:**
   The system now logs more helpful information about:
   - What variations were tried
   - What symbols are available
   - Suggestions for fixes

## Summary

✅ **What was fixed:**
- Added automatic symbol discovery
- Added support for broker-specific naming
- Better error messages and logging
- Utility scripts to help identify correct symbols

✅ **What you need to do:**
1. Run `python fix_symbols.py`
2. Follow the on-screen instructions
3. Restart your application

That's it! Your symbol naming issues should now be resolved.
