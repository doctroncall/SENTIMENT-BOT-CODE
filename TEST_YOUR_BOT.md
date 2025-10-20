# 🧪 Test Your Trading Bot - Step-by-Step Guide

## 🚀 Quick Start Testing

### **IMPORTANT: First-Time Setup**

Before testing, you need to run the symbol fixer once:

```bash
# This discovers the correct symbol names for your broker
python fix_symbols.py
```

Expected output:
```
✅ Connected to MT5 successfully!
✅ Found: GBPUSD -> GBPUSDm
✅ Found: XAUUSD -> XAUUSDm
💾 Saved symbol mapping
🎉 Your MT5 connection is working correctly!
```

---

## 🧪 Test Levels

### Level 1: Basic Connectivity ⚡ (30 seconds)
Test if MT5 connection works

### Level 2: Data Fetching 📊 (1-2 minutes)
Test if data can be retrieved

### Level 3: SMC Analysis 🎯 (2-3 minutes)
Test if analysis works

### Level 4: Full System 🚀 (3-5 minutes)
Test the complete trading system

### Level 5: GUI Testing 🖥️ (5+ minutes)
Test the graphical interface

---

## ✅ Level 1: Basic Connectivity Test

### Test MT5 Connection:

```bash
python -c "
from data_manager import DataManager

print('Testing MT5 connection...')
dm = DataManager()

if dm.connect():
    print('✅ SUCCESS: Connected to MT5')
    print(f'   Server: {dm.mt5_server}')
    print(f'   Login: {dm.mt5_login}')
    dm.disconnect()
    print('✅ Disconnected cleanly')
else:
    print('❌ FAILED: Could not connect to MT5')
"
```

**Expected Output:**
```
Testing MT5 connection...
✅ SUCCESS: Connected to MT5
   Server: ExnessKE-MT5Trial9
   Login: 211744072
✅ Disconnected cleanly
```

**If it fails:** Check credentials in `data_manager.py`

---

## 📊 Level 2: Data Fetching Test

### Test Data Retrieval:

```bash
python -c "
from data_manager import DataManager

print('Testing data fetching...')
dm = DataManager()
dm.connect()

# Fetch GBPUSD data
print('Fetching GBPUSD H1 data (last 7 days)...')
df = dm.fetch_ohlcv_for_timeframe('GBPUSD', 'H1', lookback_days=7)

if not df.empty:
    print(f'✅ SUCCESS: Fetched {len(df)} bars')
    print(f'   Date range: {df.index.min()} to {df.index.max()}')
    print(f'   Columns: {list(df.columns)}')
    print(f'   Last close: {df[\"close\"].iloc[-1]:.5f}')
else:
    print('❌ FAILED: No data retrieved')

dm.disconnect()
"
```

**Expected Output:**
```
Testing data fetching...
Fetching GBPUSD H1 data (last 7 days)...
✅ SUCCESS: Fetched 168 bars
   Date range: 2025-10-13 to 2025-10-20
   Columns: ['open', 'high', 'low', 'close', 'tick_volume']
   Last close: 1.30245
```

**If it fails:** Run `python fix_symbols.py` first

---

## 🎯 Level 3: SMC Analysis Test

### Test Market Structure Analysis:

```bash
python -c "
from data_manager import DataManager
from structure_analyzer import StructureAnalyzer

print('Testing SMC analysis...')
dm = DataManager()
dm.connect()

# Fetch data
print('Fetching GBPUSD H4 data...')
df = dm.fetch_ohlcv_for_timeframe('GBPUSD', 'H4', lookback_days=60)

if df.empty:
    print('❌ No data - cannot test analysis')
    exit(1)

print(f'✅ Got {len(df)} bars')

# Analyze
print('Running SMC analysis...')
analyzer = StructureAnalyzer(df)

# Test each component
swing_highs, swing_lows = analyzer.detect_structure()
print(f'✅ Market Structure: {len(swing_highs)} swing highs, {len(swing_lows)} swing lows')

bos = analyzer.detect_bos()
print(f'✅ BOS Detection: {len(bos)} Break of Structure points')

fvgs = analyzer.detect_fair_value_gaps()
print(f'✅ Fair Value Gaps: {len(fvgs)} FVGs detected')

obs = analyzer.detect_order_blocks()
print(f'✅ Order Blocks: {len(obs)} order blocks found')

liquidity = analyzer.detect_liquidity_zones()
print(f'✅ Liquidity Zones: {len(liquidity)} zones identified')

print(f'✅ ATR: {analyzer.avg_atr:.5f}')

print()
print('✅ SUCCESS: All SMC analysis working!')

dm.disconnect()
"
```

**Expected Output:**
```
Testing SMC analysis...
Fetching GBPUSD H4 data...
✅ Got 360 bars
Running SMC analysis...
✅ Market Structure: 15 swing highs, 14 swing lows
✅ BOS Detection: 8 Break of Structure points
✅ Fair Value Gaps: 23 FVGs detected
✅ Order Blocks: 12 order blocks found
✅ Liquidity Zones: 7 zones identified
✅ ATR: 0.00089
✅ SUCCESS: All SMC analysis working!
```

---

## 🚀 Level 4: Full System Test

### Test Complete Trading System:

```bash
python -c "
from data_manager import DataManager
from sentiment_engine import SentimentEngine
from dashboard import Dashboard

print('Testing complete trading system...')
print('='*60)

# Initialize
dm = DataManager()
dm.connect()

# Test with one symbol first
symbol = 'GBPUSD'
print(f'Testing with {symbol}...')

# Fetch multi-timeframe data
print('Fetching multi-timeframe data...')
data = dm.get_symbol_data(symbol, timeframes=['D1', 'H4', 'H1'], lookback_days=60)

print(f'✅ Fetched data for {len(data)} timeframes')
for tf, df in data.items():
    print(f'   {tf}: {len(df)} bars')

# Analyze sentiment
if data:
    print()
    print('Analyzing sentiment...')
    engine = SentimentEngine(data)
    sentiment = engine.compute_sentiment()
    
    print(f'✅ Sentiment Score: {sentiment[\"score\"]:.2f}')
    print(f'   Direction: {sentiment[\"direction\"]}')
    print(f'   Confidence: {sentiment[\"confidence\"]:.1%}')
    print(f'   Recommendation: {sentiment.get(\"recommendation\", \"N/A\")}')

print()
print('✅ SUCCESS: Full system working!')

dm.disconnect()
"
```

**Expected Output:**
```
Testing complete trading system...
============================================================
Testing with GBPUSD...
Fetching multi-timeframe data...
✅ Fetched data for 3 timeframes
   D1: 60 bars
   H4: 360 bars
   H1: 1440 bars
Analyzing sentiment...
✅ Sentiment Score: 0.68
   Direction: BULLISH
   Confidence: 68.5%
   Recommendation: BUY
✅ SUCCESS: Full system working!
```

---

## 🖥️ Level 5: GUI Test

### Test Streamlit GUI:

```bash
streamlit run gui.py
```

**What to test in GUI:**

1. **Dashboard Tab:**
   - Should load without errors
   - Should show system status
   - Check if symbols are displayed

2. **Data Tab:**
   - Enter: GBPUSD
   - Timeframe: H1
   - Days: 7
   - Click "Fetch Data"
   - **Expected:** Data table appears with OHLC values

3. **Analysis Tab:**
   - Click "Run Analysis"
   - **Expected:** Analysis runs and shows results

4. **Sentiment Tab:**
   - Should show sentiment scores
   - Check for BUY/SELL signals

**Expected:** GUI loads and all features work ✅

---

## 🔧 Test with Multiple Symbols

### Test Multiple Symbols:

```bash
python -c "
from data_manager import DataManager

symbols = ['GBPUSD', 'XAUUSD', 'EURUSD']
dm = DataManager()
dm.connect()

print('Testing multiple symbols...')
print('='*60)

for symbol in symbols:
    print(f'Testing {symbol}...')
    df = dm.fetch_ohlcv_for_timeframe(symbol, 'H1', lookback_days=2)
    
    if not df.empty:
        print(f'  ✅ {len(df)} bars, last close: {df[\"close\"].iloc[-1]:.5f}')
    else:
        print(f'  ❌ Failed to fetch data')

dm.disconnect()
print()
print('✅ Multi-symbol test complete!')
"
```

---

## 🎯 Quick Test Script

I'll create an all-in-one test script:

```bash
python test_bot.py
```

This will run all tests automatically!

---

## ❌ Troubleshooting

### Problem: "Symbol not found"
**Solution:**
```bash
python fix_symbols.py
```

### Problem: "Connection failed"
**Check:**
1. MT5 terminal is running
2. Credentials are correct in `data_manager.py`
3. Internet connection is active

### Problem: "No data returned"
**Check:**
```bash
python list_mt5_symbols.py --search GBPUSD
```
See what symbols are actually available

### Problem: "Import errors"
**Solution:**
```bash
pip install -r requirements.txt
```

---

## ✅ Success Checklist

Mark each when complete:

- [ ] Level 1: MT5 connection works
- [ ] Level 2: Data fetching works
- [ ] Level 3: SMC analysis works
- [ ] Level 4: Full system works
- [ ] Level 5: GUI loads and works
- [ ] Multi-symbol test passes
- [ ] No error messages
- [ ] Ready for live use!

---

## 🚀 Next Steps After Testing

Once all tests pass:

1. **Configure your symbols:**
   - Edit `config/gui_config.json`
   - Add your preferred trading pairs

2. **Adjust timeframes:**
   - Default: D1, H4, H1
   - Modify based on your strategy

3. **Set risk parameters:**
   - Configure in settings tab

4. **Start trading:**
   - Run analysis
   - Review signals
   - Execute trades

---

## 📊 Performance Benchmarks

Your system should achieve:

- **Connection:** < 2 seconds
- **Data fetch (7 days H1):** < 5 seconds
- **SMC analysis:** < 3 seconds
- **Full analysis (3 timeframes):** < 15 seconds
- **GUI load:** < 10 seconds

If slower, check network connection or MT5 server.

---

## 🎉 You're Ready!

Once all tests pass, your bot is ready for:
- ✅ Live analysis
- ✅ Signal generation
- ✅ Trading decisions
- ✅ Production use

**Good luck with your trading! 📈**
