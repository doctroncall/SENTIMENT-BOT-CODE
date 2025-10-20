"""
Data Analysis Report - Check if we have all required data for SMC and indicators
"""

import pandas as pd
import numpy as np

# Current data structure being fetched
CURRENT_COLUMNS = ["time", "open", "high", "low", "close", "tick_volume"]

# MT5 provides these fields in rates structure
MT5_AVAILABLE_FIELDS = [
    "time",           # Bar open time
    "open",           # Open price
    "high",           # High price
    "low",            # Low price
    "close",          # Close price
    "tick_volume",    # Tick volume (number of ticks)
    "real_volume",    # Real volume (actual traded volume, if broker provides it)
    "spread",         # Spread in points at bar close
]

# Required for Technical Indicators
INDICATOR_REQUIREMENTS = {
    "Moving Averages (SMA, EMA, WMA)": ["close"],
    "RSI (Relative Strength Index)": ["close"],
    "MACD": ["close"],
    "Bollinger Bands": ["close"],
    "Stochastic Oscillator": ["high", "low", "close"],
    "ATR (Average True Range)": ["high", "low", "close"],
    "ADX (Directional Movement)": ["high", "low", "close"],
    "Parabolic SAR": ["high", "low", "close"],
    "CCI (Commodity Channel Index)": ["high", "low", "close"],
    "Williams %R": ["high", "low", "close"],
    "Momentum": ["close"],
    "ROC (Rate of Change)": ["close"],
    "OBV (On Balance Volume)": ["close", "volume"],
    "Volume Indicators": ["volume"],
    "VWAP": ["high", "low", "close", "volume"],
}

# Required for SMC (Smart Money Concepts)
SMC_REQUIREMENTS = {
    "Market Structure (BOS/CHoCH)": {
        "required": ["high", "low", "close"],
        "optional": ["volume"],
        "description": "Identify swing highs/lows and break of structure"
    },
    "Fair Value Gaps (FVG/Imbalance)": {
        "required": ["open", "high", "low", "close"],
        "optional": [],
        "description": "3-candle pattern with gap between candle 1 and 3"
    },
    "Order Blocks": {
        "required": ["open", "high", "low", "close"],
        "optional": ["volume", "tick_volume"],
        "description": "Last opposing candle before strong move"
    },
    "Liquidity Zones": {
        "required": ["high", "low"],
        "optional": ["volume"],
        "description": "Areas of equal highs/lows or sweep zones"
    },
    "Premium/Discount Zones": {
        "required": ["high", "low"],
        "optional": [],
        "description": "50% retracement levels of swing ranges"
    },
    "Breaker Blocks": {
        "required": ["open", "high", "low", "close"],
        "optional": [],
        "description": "Failed order blocks that break and reverse"
    },
    "Mitigation Blocks": {
        "required": ["open", "high", "low", "close"],
        "optional": [],
        "description": "Price returning to origin zones"
    },
    "Inducement Zones": {
        "required": ["high", "low"],
        "optional": [],
        "description": "Fake-out levels designed to trap traders"
    },
    "Volume Analysis": {
        "required": ["close"],
        "optional": ["volume", "tick_volume"],
        "description": "High volume at key levels confirms smart money"
    },
    "Market Maker Models": {
        "required": ["open", "high", "low", "close"],
        "optional": [],
        "description": "Accumulation, Manipulation, Distribution patterns"
    }
}

# What we're CURRENTLY fetching
CURRENTLY_FETCHED = set(["time", "open", "high", "low", "close", "tick_volume"])

# What we SHOULD be fetching
SHOULD_FETCH = set(["time", "open", "high", "low", "close", "tick_volume", "real_volume", "spread"])


def check_data_completeness():
    """Check if current data is sufficient"""
    
    print("\n" + "="*80)
    print("DATA COMPLETENESS ANALYSIS")
    print("="*80 + "\n")
    
    print("📊 CURRENT DATA BEING FETCHED:")
    print("-" * 50)
    for col in sorted(CURRENT_COLUMNS):
        print(f"  ✓ {col}")
    print()
    
    print("🔍 MT5 PROVIDES THESE ADDITIONAL FIELDS:")
    print("-" * 50)
    missing = set(MT5_AVAILABLE_FIELDS) - CURRENTLY_FETCHED
    for field in sorted(missing):
        print(f"  ⚠️  {field} - NOT BEING CAPTURED")
    print()
    
    # Check indicator requirements
    print("📈 TECHNICAL INDICATOR REQUIREMENTS:")
    print("-" * 50)
    all_satisfied = True
    for indicator, requirements in INDICATOR_REQUIREMENTS.items():
        required_set = set(req.replace("volume", "tick_volume") for req in requirements)
        has_all = required_set.issubset(CURRENTLY_FETCHED)
        status = "✅" if has_all else "❌"
        print(f"  {status} {indicator}")
        if not has_all:
            missing = required_set - CURRENTLY_FETCHED
            print(f"      Missing: {', '.join(missing)}")
            all_satisfied = False
    print()
    
    # Check SMC requirements
    print("🎯 SMART MONEY CONCEPTS (SMC) REQUIREMENTS:")
    print("-" * 50)
    smc_satisfied = True
    for concept, info in SMC_REQUIREMENTS.items():
        required_set = set(info["required"])
        optional_set = set(info["optional"])
        
        has_all_required = required_set.issubset(CURRENTLY_FETCHED)
        has_optional = any(opt in CURRENTLY_FETCHED for opt in optional_set) if optional_set else True
        
        status = "✅" if has_all_required else "⚠️"
        print(f"  {status} {concept}")
        print(f"      {info['description']}")
        
        if not has_all_required:
            missing = required_set - CURRENTLY_FETCHED
            print(f"      ❌ Missing required: {', '.join(missing)}")
            smc_satisfied = False
        
        if optional_set:
            missing_optional = optional_set - CURRENTLY_FETCHED
            if missing_optional:
                print(f"      ⚠️  Missing optional: {', '.join(missing_optional)}")
        print()
    
    # Summary
    print("="*80)
    print("SUMMARY")
    print("="*80 + "\n")
    
    print("✅ HAVE (Currently Fetched):")
    for col in sorted(CURRENTLY_FETCHED):
        use_case = []
        if col in ["open", "high", "low", "close"]:
            use_case.append("Price action")
            use_case.append("SMC patterns")
            use_case.append("Indicators")
        elif col == "tick_volume":
            use_case.append("Volume analysis")
        elif col == "time":
            use_case.append("Time-based analysis")
        
        print(f"  ✓ {col:15s} → {', '.join(use_case)}")
    print()
    
    print("⚠️  MISSING (Could Enhance Analysis):")
    should_add = SHOULD_FETCH - CURRENTLY_FETCHED
    for field in sorted(should_add):
        if field == "real_volume":
            print(f"  • {field:15s} → Actual traded volume (more accurate than tick volume)")
            print(f"                      Useful for: Volume profile, institutional activity")
        elif field == "spread":
            print(f"  • {field:15s} → Bid/Ask spread at candle close")
            print(f"                      Useful for: Liquidity analysis, execution quality")
    print()
    
    # Recommendations
    print("="*80)
    print("RECOMMENDATIONS")
    print("="*80 + "\n")
    
    if smc_satisfied and all_satisfied:
        print("✅ EXCELLENT: Current data is SUFFICIENT for:")
        print("   • All technical indicators")
        print("   • All SMC concepts")
        print("   • Market structure analysis")
        print()
    else:
        print("⚠️  GOOD: Current data works for most analysis, but consider:")
        print()
    
    print("💡 SUGGESTED ENHANCEMENTS:")
    print("-" * 50)
    print("1. Add 'real_volume' field:")
    print("   - More accurate than tick_volume")
    print("   - Better for volume-based SMC confirmation")
    print("   - Note: Not all brokers provide this")
    print()
    print("2. Add 'spread' field:")
    print("   - Useful for liquidity analysis")
    print("   - Helps identify tight vs wide spread zones")
    print("   - Can indicate institutional activity")
    print()
    print("3. Keep 'tick_volume' as fallback:")
    print("   - Still useful when real_volume not available")
    print("   - Better than no volume data")
    print()
    
    print("="*80)
    print("CONCLUSION")
    print("="*80 + "\n")
    
    print("Current Status:")
    print(f"  • OHLC Data: ✅ Complete (open, high, low, close)")
    print(f"  • Volume Data: ✅ Available (tick_volume)")
    print(f"  • Time Data: ✅ Available (UTC timestamps)")
    print(f"  • Technical Indicators: ✅ Fully Supported")
    print(f"  • SMC Analysis: ✅ Fully Supported")
    print()
    print(f"Enhancement Opportunities:")
    print(f"  • Real Volume: ⚠️  Not captured (could add if broker provides)")
    print(f"  • Spread Data: ⚠️  Not captured (could add for liquidity analysis)")
    print()
    print("Overall Assessment: ✅ SUFFICIENT FOR ALL CURRENT NEEDS")
    print()


if __name__ == "__main__":
    check_data_completeness()
