"""Test script for divergence detection tool."""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.divergence import get_divergence_detection


async def test_divergence_detection():
    """Test divergence detection with a real stock."""
    print("=" * 60)
    print("TESTING DIVERGENCE DETECTION")
    print("=" * 60)
    
    # Test with BBCA
    ticker = "BBCA"
    print(f"\n📊 Testing divergence detection for {ticker}...")
    
    try:
        result = await get_divergence_detection({
            "ticker": ticker,
            "indicators": ["rsi", "macd", "obv"],
            "lookback": 30,
            "period": "3mo"
        })
        
        print(f"\n✅ SUCCESS!")
        print(f"Ticker: {result['ticker']}")
        print(f"Analysis Date: {result['analysis_date']}")
        print(f"Current Price: {result['current_price']}")
        print(f"Price Change: {result['price_change']} ({result['price_change_pct']:.2f}%)")
        
        # Per-indicator analysis
        print(f"\n📈 Indicator Analyses:")
        for analysis in result['indicator_analyses']:
            print(f"\n  {analysis['indicator']}:")
            print(f"    Current Value: {analysis['current_value']}")
            print(f"    Regular Divergences: {len(analysis['regular_divergences'])}")
            print(f"    Hidden Divergences: {len(analysis['hidden_divergences'])}")
            
            if analysis['active_divergence']:
                ad = analysis['active_divergence']
                print(f"    ⚡ ACTIVE: {ad['type']} ({ad['strength']})")
                print(f"       Signal: {ad['signal']}")
        
        # Overall signal
        print(f"\n🎯 Overall Signal:")
        overall = result['overall_signal']
        print(f"  Signal: {overall['signal']}")
        print(f"  Action: {overall['action']}")
        print(f"  Confidence: {overall['confidence']}")
        print(f"  Bullish Score: {overall['bullish_score']}")
        print(f"  Bearish Score: {overall['bearish_score']}")
        print(f"  Indicator Agreement: {overall['indicator_agreement']}")
        
        if overall['active_divergences']:
            print(f"\n  Active Divergences:")
            for ad in overall['active_divergences']:
                print(f"    - {ad['indicator']}: {ad['type']} ({ad['strength']})")
        
        # Insights
        print(f"\n💡 Insights:")
        for insight in result['insights']:
            print(f"  {insight}")
        
        # Educational note
        print(f"\n📚 Educational Note:")
        edu = result['educational_note']
        print(f"  Regular: {edu['regular_divergence']}")
        print(f"  Hidden: {edu['hidden_divergence']}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_multiple_stocks():
    """Test divergence detection with multiple stocks."""
    print("\n" + "=" * 60)
    print("TESTING MULTIPLE STOCKS")
    print("=" * 60)
    
    tickers = ["BBRI", "TLKM", "SMGR"]
    
    for ticker in tickers:
        print(f"\n{'─' * 40}")
        print(f"Testing {ticker}...")
        
        try:
            result = await get_divergence_detection({
                "ticker": ticker,
                "indicators": ["rsi", "macd"],
                "lookback": 30,
                "period": "3mo"
            })
            
            overall = result['overall_signal']
            
            print(f"  Price: {result['current_price']} ({result['price_change_pct']:+.2f}%)")
            print(f"  Signal: {overall['signal']}")
            print(f"  Action: {overall['action']}")
            print(f"  Confidence: {overall['confidence']}")
            
            if overall['active_divergences']:
                active_str = ', '.join([f"{d['indicator']} {d['type']}" for d in overall['active_divergences']])
                print(f"  Active: {active_str}")
            else:
                print(f"  Active: No divergence detected")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")


async def test_single_indicator():
    """Test divergence detection with single indicator."""
    print("\n" + "=" * 60)
    print("TESTING SINGLE INDICATOR (RSI)")
    print("=" * 60)
    
    ticker = "BBCA"
    print(f"\nTesting {ticker} with RSI only...")
    
    try:
        result = await get_divergence_detection({
            "ticker": ticker,
            "indicators": ["rsi"],
            "lookback": 30,
            "period": "6mo"  # Longer period for more data
        })
        
        rsi_analysis = result['indicator_analyses'][0]
        
        print(f"\n  RSI Current: {rsi_analysis['current_value']}")
        print(f"  Regular Divergences Found: {len(rsi_analysis['regular_divergences'])}")
        print(f"  Hidden Divergences Found: {len(rsi_analysis['hidden_divergences'])}")
        
        # Show details of divergences found
        for div in rsi_analysis['regular_divergences'][:3]:  # Show max 3
            print(f"\n  📊 {div['type'].upper()}:")
            print(f"     Price: {div['start_price']} → {div['end_price']} ({div['price_pattern']})")
            print(f"     RSI: {div['start_indicator']} → {div['end_indicator']} ({div['indicator_pattern']})")
            print(f"     Strength: {div['strength']}")
            print(f"     Bars Apart: {div['bars_apart']}")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n🔧 Running Divergence Detection Tests\n")
    
    # Run tests
    asyncio.run(test_divergence_detection())
    asyncio.run(test_multiple_stocks())
    asyncio.run(test_single_indicator())
    
    print("\n" + "=" * 60)
    print("✅ TESTING COMPLETE")
    print("=" * 60)

