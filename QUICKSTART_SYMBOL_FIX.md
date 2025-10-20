# 🚀 QUICK START - Fix Symbol Issues

## Your Error
```
MT5 fetch failed for GBPUSD D1: Symbol GBPUSD not found in MT5
```

## The Solution (3 Easy Steps)

### Step 1: Run the Fix Tool

**Windows:**
Double-click: `fix_symbols.bat`

**Linux/Mac:**
```bash
./fix_symbols.sh
```

**Or:**
```bash
python fix_symbols.py
```

### Step 2: Wait for Results
The tool will:
- ✅ Connect to your MT5
- 🔍 Find correct symbol names
- 💾 Save the configuration
- 🧪 Test everything

### Step 3: Restart Your GUI
```bash
streamlit run gui.py
```

## That's It! 🎉

Your symbols should now work correctly.

---

## What If It Doesn't Work?

### Option A: See All Available Symbols
```bash
python list_mt5_symbols.py --all
```

### Option B: Search for Specific Symbol
```bash
python list_mt5_symbols.py --search GBPUSD
```

### Option C: Manual Check
1. Open MT5 Terminal
2. Press `Ctrl+M` (Market Watch)
3. Right-click → "Symbols"
4. Search for your pair (e.g., GBPUSD)
5. Note the EXACT name shown

---

## Need More Help?

📖 Read: `SYMBOL_FIX_GUIDE.md` - Detailed explanation  
📖 Read: `FIXES_APPLIED_SYMBOL_ISSUE.md` - What was changed

---

## Quick Test

After running the fix, test it:

```python
from data_manager import DataManager

dm = DataManager()
dm.connect()

df = dm.fetch_ohlcv_for_timeframe("GBPUSD", "H1", lookback_days=7)
print(f"✅ Success! Fetched {len(df)} bars")

dm.disconnect()
```

---

**Remember:** The system now automatically discovers correct symbol names, so you should only need to run this once!
