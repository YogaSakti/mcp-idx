#!/usr/bin/env python3
"""Test Candlestick pattern detection with real Indonesian stocks."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.tools.candlestick import get_candlestick_patterns


async def test_candlestick_patterns():
    """Test candlestick patterns with BBCA, BBRI, HMSP."""

    test_tickers = ["BBCA.JK", "BBRI.JK", "HMSP.JK"]

    for ticker in test_tickers:
        print(f"\n{'='*70}")
        print(f"Testing Candlestick Patterns: {ticker}")
        print(f"{'='*70}")

        try:
            result = await get_candlestick_patterns({
                "ticker": ticker,
                "period": "1mo",
                "lookback_days": 10
            })

            if "error" in result:
                print(f"❌ Error: {result['error']}")
                continue

            print(f"\n📊 Current Price: Rp {result['current_price']:,.2f}")
            print(f"📅 Lookback Period: {result['lookback_days']} days")
            print(f"🔍 Patterns Detected: {result['patterns_detected']}")

            # Summary
            if "summary" in result:
                summary = result["summary"]
                print(f"\n📈 Pattern Summary:")
                print(f"   Bullish: {summary['bullish_count']} pattern(s)")
                print(f"   Bearish: {summary['bearish_count']} pattern(s)")
                print(f"   Neutral: {summary['neutral_count']} pattern(s)")

            # List all patterns
            if result['patterns_detected'] > 0:
                print(f"\n🕯️  Detected Patterns:")
                for pattern in result['patterns']:
                    signal_icon = {"bullish": "🟢", "bearish": "🔴", "neutral": "🟡"}.get(pattern['signal'], "⚪")
                    strength_map = {"very_strong": "⭐⭐⭐", "strong": "⭐⭐", "medium": "⭐"}
                    strength = strength_map.get(pattern['strength'], "")

                    print(f"\n   {signal_icon} {pattern['pattern']} - {pattern['date']}")
                    print(f"      Type: {pattern['type'].capitalize()} {strength}")
                    print(f"      Signal: {pattern['signal'].upper()}")
                    print(f"      {pattern['description']}")
            else:
                print(f"\n⚪ No patterns detected in the lookback period")

            # Trading insights
            if "insights" in result and result["insights"]:
                print(f"\n💡 Trading Insights:")
                for insight in result["insights"]:
                    print(f"   {insight}")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_candlestick_patterns())
