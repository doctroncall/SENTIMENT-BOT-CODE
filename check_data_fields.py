"""
Quick utility to check what data fields are being fetched and what's available
"""

from data_manager import DataManager
import pandas as pd

def check_data_fields():
    print("\n" + "="*80)
    print("DATA FIELDS CHECK")
    print("="*80 + "\n")
    
    dm = DataManager()
    
    print("Connecting to MT5...")
    if not dm.connect():
        print("❌ Failed to connect to MT5")
        return
    
    print("✅ Connected!\n")
    
    # Try to fetch a small amount of data
    print("Fetching sample data for GBPUSD H1...")
    try:
        df = dm.fetch_ohlcv_for_timeframe("GBPUSD", "H1", lookback_days=2)
        
        if df.empty:
            print("❌ No data returned")
            return
        
        print(f"✅ Fetched {len(df)} bars\n")
        
        print("="*80)
        print("AVAILABLE DATA FIELDS")
        print("="*80 + "\n")
        
        print("Columns in DataFrame:")
        for i, col in enumerate(df.columns, 1):
            sample_value = df[col].iloc[-1] if len(df) > 0 else "N/A"
            print(f"  {i}. {col:15s} → Last value: {sample_value}")
        
        print(f"\nData shape: {len(df)} rows × {len(df.columns)} columns")
        
        print("\n" + "="*80)
        print("SAMPLE DATA (Last 3 bars)")
        print("="*80 + "\n")
        print(df.tail(3).to_string())
        
        print("\n" + "="*80)
        print("DATA COMPLETENESS CHECK")
        print("="*80 + "\n")
        
        required_for_indicators = ['open', 'high', 'low', 'close']
        required_for_smc = ['open', 'high', 'low', 'close']
        optional_for_volume = ['tick_volume', 'real_volume']
        optional_for_liquidity = ['spread']
        
        print("Core OHLC Data:")
        for field in required_for_indicators:
            status = "✅" if field in df.columns else "❌"
            print(f"  {status} {field}")
        
        print("\nVolume Data:")
        has_volume = False
        for field in optional_for_volume:
            if field in df.columns:
                print(f"  ✅ {field}")
                has_volume = True
        if not has_volume:
            print("  ⚠️  No volume data available")
        
        print("\nLiquidity Data:")
        has_liquidity = False
        for field in optional_for_liquidity:
            if field in df.columns:
                print(f"  ✅ {field}")
                has_liquidity = True
        if not has_liquidity:
            print("  ℹ️  No spread data (optional)")
        
        print("\n" + "="*80)
        print("ASSESSMENT")
        print("="*80 + "\n")
        
        can_do_indicators = all(f in df.columns for f in required_for_indicators)
        can_do_smc = all(f in df.columns for f in required_for_smc)
        
        if can_do_indicators and can_do_smc:
            print("✅ EXCELLENT: All required data available!")
            print("\nYou can perform:")
            print("  ✓ All technical indicators")
            print("  ✓ All SMC analysis")
            print("  ✓ Market structure detection")
            if has_volume:
                print("  ✓ Volume-based analysis")
            if has_liquidity:
                print("  ✓ Liquidity/spread analysis")
        else:
            print("⚠️  WARNING: Missing some required data")
            if not can_do_indicators:
                missing = [f for f in required_for_indicators if f not in df.columns]
                print(f"  Missing for indicators: {', '.join(missing)}")
            if not can_do_smc:
                missing = [f for f in required_for_smc if f not in df.columns]
                print(f"  Missing for SMC: {', '.join(missing)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        dm.disconnect()
        print("\n✅ Disconnected from MT5\n")


if __name__ == "__main__":
    check_data_fields()
