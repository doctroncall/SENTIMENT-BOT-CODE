#!/usr/bin/env python3
"""
Test script for Data Collection Status Tracker
Demonstrates the new real-time tracking functionality
"""

import time
from data_manager import get_collection_status

def test_collection_tracker():
    """Test the data collection status tracker"""
    
    print("=" * 70)
    print("Testing Data Collection Status Tracker")
    print("=" * 70)
    
    # Get tracker instance
    tracker = get_collection_status()
    print("\n✅ Tracker initialized")
    
    # Simulate a collection cycle
    print("\n📊 Simulating data collection for 3 symbols...")
    
    symbols = ['GBPUSD', 'XAUUSD', 'EURUSD']
    timeframes = ['D1', 'H4', 'H1']
    
    # Start collection
    tracker.start_collection(symbols)
    print(f"\n🚀 Collection started for: {symbols}")
    status = tracker.get_status()
    print(f"   Status: {status['current_status']}")
    print(f"   Queue: {status['symbols_queue']}")
    
    # Process each symbol
    for symbol in symbols:
        print(f"\n{'─' * 70}")
        print(f"Processing {symbol}...")
        
        tracker.start_symbol(symbol)
        status = tracker.get_status()
        print(f"   Current symbol: {status['current_symbol']}")
        print(f"   Status: {status['current_status']}")
        
        # Process each timeframe
        for tf in timeframes:
            tracker.start_timeframe(symbol, tf)
            status = tracker.get_status()
            print(f"   → Fetching {tf}... ", end="")
            
            # Simulate data fetch (would normally call MT5 here)
            time.sleep(0.3)
            
            # Simulate success with random bar count
            import random
            bars = random.randint(100, 300)
            tracker.complete_timeframe(symbol, tf, bars)
            print(f"✅ {bars} bars")
        
        # Mark symbol complete
        tracker.complete_symbol(symbol, success=True)
        status = tracker.get_status()
        print(f"   ✅ {symbol} completed")
        print(f"   Completed: {status['symbols_completed']}")
        print(f"   Remaining: {status['symbols_queue']}")
    
    # Final status
    print(f"\n{'=' * 70}")
    print("Collection Complete!")
    print("=" * 70)
    
    final_status = tracker.get_status()
    print(f"\n📊 Final Statistics:")
    print(f"   Total symbols: {final_status['total_symbols']}")
    print(f"   ✅ Completed: {len(final_status['symbols_completed'])}")
    print(f"   ❌ Failed: {len(final_status['symbols_failed'])}")
    print(f"   ⏳ Queued: {len(final_status['symbols_queue'])}")
    
    print(f"\n📋 Detailed Results:")
    for symbol, tf_data in final_status['timeframe_data'].items():
        total_bars = sum(data.get('bars', 0) for data in tf_data.values())
        print(f"   {symbol}:")
        for tf, data in tf_data.items():
            status_icon = "✅" if data.get('status') == 'complete' else "❌"
            print(f"      {status_icon} {tf}: {data.get('bars', 0)} bars")
        print(f"      Total: {total_bars} bars")
    
    print("\n✅ Test completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    try:
        test_collection_tracker()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
