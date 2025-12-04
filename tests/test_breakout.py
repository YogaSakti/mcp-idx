"""Test script for breakout detection tool."""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.breakout import get_breakout_detection


async def test_breakout_detection():
    """Test breakout detection with a real stock."""
    print("=" * 60)
    print("TESTING BREAKOUT DETECTION")
    print("=" * 60)
    
    # Test with BBCA
    ticker = "BBCA"
    print(f"\n📊 Testing breakout detection for {ticker}...")
    
    try:
        result = await get_breakout_detection({
            "ticker": ticker,
            "lookback": 20,
            "period": "3mo",
            "volume_threshold": 1.5
        })
        
        print(f"\n✅ SUCCESS!")
        print(f"Ticker: {result['ticker']}")
        print(f"Analysis Date: {result['analysis_date']}")
        print(f"Current Price: {result['current_price']}")
        print(f"Price Change: {result['price_change']} ({result['price_change_pct']:.2f}%)")
        
        # Consolidation range
        print(f"\n📈 Consolidation Range:")
        cons = result['consolidation_range']
        print(f"  Support: {cons['support']}")
        print(f"  Resistance: {cons['resistance']}")
        print(f"  Range Size: {cons['range_size']} ({cons['range_pct']:.2f}%)")
        print(f"  Is Consolidating: {cons['is_consolidating']}")
        
        # Breakout analysis
        print(f"\n🚀 Breakout Analysis:")
        bo = result['breakout_analysis']
        print(f"  Type: {bo['breakout_type']}")
        print(f"  Strength: {bo['breakout_strength']}")
        print(f"  Volume Ratio: {bo['volume_ratio']}x")
        print(f"  Volume Confirmed: {bo['volume_confirmed']}")
        if bo['targets']:
            print(f"  Targets: {bo['targets']}")
        if bo['stop_loss']:
            print(f"  Stop Loss: {bo['stop_loss']}")
        if bo['risk_reward_ratio']:
            print(f"  Risk/Reward: {bo['risk_reward_ratio']}")
        
        # False breakout check
        print(f"\n⚠️ False Breakout Check:")
        fb = result['false_breakout_check']
        print(f"  Has Warning: {fb['has_warning']}")
        if fb['warnings']:
            for w in fb['warnings']:
                print(f"    - {w}")
        
        # Signal
        print(f"\n🎯 Signal:")
        sig = result['signal']
        print(f"  Signal: {sig['signal']}")
        print(f"  Action: {sig['action']}")
        print(f"  Confidence: {sig['confidence']}")
        
        # Insights
        print(f"\n💡 Insights:")
        for insight in result['insights']:
            print(f"  {insight}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_multiple_stocks():
    """Test breakout detection with multiple stocks."""
    print("\n" + "=" * 60)
    print("TESTING MULTIPLE STOCKS")
    print("=" * 60)
    
    tickers = ["BBRI", "TLKM", "SMGR"]
    
    for ticker in tickers:
        print(f"\n{'─' * 40}")
        print(f"Testing {ticker}...")
        
        try:
            result = await get_breakout_detection({
                "ticker": ticker,
                "lookback": 20,
                "period": "3mo"
            })
            
            bo = result['breakout_analysis']
            sig = result['signal']
            cons = result['consolidation_range']
            
            print(f"  Price: {result['current_price']} ({result['price_change_pct']:+.2f}%)")
            print(f"  Range: {cons['support']} - {cons['resistance']}")
            print(f"  Type: {bo['breakout_type']}")
            print(f"  Strength: {bo['breakout_strength']}")
            print(f"  Signal: {sig['signal']} | Action: {sig['action']}")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")


if __name__ == "__main__":
    print("\n🔧 Running Breakout Detection Tests\n")
    
    # Run tests
    asyncio.run(test_breakout_detection())
    asyncio.run(test_multiple_stocks())
    
    print("\n" + "=" * 60)
    print("✅ TESTING COMPLETE")
    print("=" * 60)

