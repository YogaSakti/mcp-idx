#!/usr/bin/env python3
"""
Test Candlestick pattern detection with real Indonesian stocks.
UPDATED: Includes trend context validation, volume confirmation, and new patterns.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.candlestick import get_candlestick_patterns


async def test_candlestick_patterns():
    """Test candlestick patterns with BBCA, BBRI, CDIA."""

    test_tickers = ["BBCA", "BBRI", "CDIA", "CUAN"]

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

            # Test JSON serialization first
            try:
                json_str = json.dumps(result, indent=2, default=str)
                print(f"✅ JSON serialization: OK")
            except Exception as e:
                print(f"❌ JSON serialization FAILED: {e}")
                continue

            if "error" in result:
                print(f"❌ Error: {result['error']}")
                continue

            print(f"\n📊 Current Price: Rp {result['current_price']:,.2f}")
            print(f"📅 Lookback Period: {result['lookback_days']} days")
            print(f"📈 Data Points: {result.get('data_points', 'N/A')}")
            print(f"🔍 Patterns Detected: {result['patterns_detected']}")
            
            # NEW: Valid vs Weak patterns
            valid_count = result.get('valid_patterns_count', 'N/A')
            weak_count = result.get('weak_patterns_count', 'N/A')
            print(f"   ✅ Valid: {valid_count} | ⚠️ Weak: {weak_count}")

            # NEW: Volume confirmation
            vol_conf = result.get('volume_confirmation', {})
            if vol_conf:
                print(f"📦 Volume Confirmation: {vol_conf.get('confirmed_count', 0)} patterns ({vol_conf.get('confirmation_rate', 0)}%)")

            # NEW: Overall signal
            overall = result.get('overall_signal', 'N/A')
            signal_icon = {"bullish": "🟢", "bearish": "🔴", "neutral": "🟡"}.get(overall, "⚪")
            print(f"🎯 Overall Signal: {signal_icon} {overall.upper()}")

            # Summary
            if "summary" in result:
                summary = result["summary"]
                print(f"\n📈 Pattern Summary:")
                # NEW: Updated field names
                bullish = summary.get('bullish_valid', summary.get('bullish_count', 0))
                bearish = summary.get('bearish_valid', summary.get('bearish_count', 0))
                neutral = summary.get('neutral_count', 0)
                print(f"   Bullish (valid): {bullish} pattern(s)")
                print(f"   Bearish (valid): {bearish} pattern(s)")
                print(f"   Neutral: {neutral} pattern(s)")

            # List all patterns with new fields
            if result['patterns_detected'] > 0:
                print(f"\n🕯️  Detected Patterns:")
                for pattern in result['patterns']:
                    signal_icon = {"bullish": "🟢", "bearish": "🔴", "neutral": "🟡"}.get(pattern['signal'], "⚪")
                    strength_map = {"very_strong": "⭐⭐⭐", "strong": "⭐⭐", "medium": "⭐", "weak": ""}
                    strength = strength_map.get(pattern['strength'], "")
                    
                    # NEW: Validity indicator
                    is_valid = pattern.get('is_valid', True)
                    valid_icon = "✓" if is_valid else "⚠️"

                    print(f"\n   {signal_icon} {pattern['pattern']} - {pattern['date']} {valid_icon}")
                    print(f"      Type: {pattern['type'].capitalize()} {strength}")
                    print(f"      Signal: {pattern['signal'].upper()}")
                    
                    # NEW: Trend context
                    trend = pattern.get('trend_context', 'N/A')
                    price_vs_ma = pattern.get('price_vs_ma', 'N/A')
                    print(f"      Trend Context: {trend} | Price vs MA: {price_vs_ma}")
                    
                    # NEW: Volume confirmation
                    vol_confirmed = pattern.get('volume_confirmed', False)
                    vol_icon = "📦" if vol_confirmed else "📭"
                    print(f"      Volume Confirmed: {vol_icon} {vol_confirmed}")
                    
                    # NEW: Validity status
                    print(f"      Valid Pattern: {'✅ YES' if is_valid else '⚠️ NO (wrong trend context)'}")
                    
                    # NEW: Potential ARA
                    if pattern.get('potential_ara'):
                        print(f"      🚀 POTENTIAL ARA!")
                    
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


async def test_json_serialization():
    """Test that all outputs can be JSON serialized (no numpy types)."""
    print("\n" + "="*70)
    print("Testing JSON Serialization for All Fields")
    print("="*70)
    
    result = await get_candlestick_patterns({
        "ticker": "BBRI",
        "period": "1mo",
        "lookback_days": 10
    })
    
    if "error" in result:
        print(f"❌ Error getting data: {result['error']}")
        return
    
    # Check each pattern's fields
    all_ok = True
    for i, pattern in enumerate(result.get('patterns', [])):
        for key, value in pattern.items():
            try:
                json.dumps({key: value})
            except TypeError as e:
                print(f"❌ Pattern {i}, field '{key}': {type(value).__name__} not serializable")
                all_ok = False
    
    if all_ok:
        print("✅ All pattern fields are JSON serializable")
    
    # Test full result
    try:
        json.dumps(result)
        print("✅ Full result is JSON serializable")
    except TypeError as e:
        print(f"❌ Full result not serializable: {e}")


async def test_new_patterns():
    """Test that new patterns (Marubozu, Hanging Man, Inverted Hammer) are detected."""
    print("\n" + "="*70)
    print("Testing New Pattern Types")
    print("="*70)
    
    # Use 3mo for more data
    result = await get_candlestick_patterns({
        "ticker": "BBRI",
        "period": "3mo",
        "lookback_days": 30
    })
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return
    
    pattern_types = set()
    for pattern in result.get('patterns', []):
        pattern_types.add(pattern['pattern'])
    
    print(f"Pattern types found: {sorted(pattern_types)}")
    
    new_patterns = ["Marubozu", "Hanging Man", "Inverted Hammer"]
    for np in new_patterns:
        if np in pattern_types:
            print(f"✅ {np} detected")
        else:
            print(f"⚪ {np} not found (may not be present in data)")


if __name__ == "__main__":
    print("🕯️  CANDLESTICK PATTERN DETECTION TEST")
    print("="*70)
    print("Testing IDX-optimized candlestick detection with:")
    print("- Trend context validation")
    print("- Volume confirmation")
    print("- Adaptive doji threshold (for gocap stocks)")
    print("- New patterns (Marubozu, Hanging Man, Inverted Hammer)")
    
    asyncio.run(test_candlestick_patterns())
    asyncio.run(test_json_serialization())
    asyncio.run(test_new_patterns())
    
    print("\n" + "="*70)
    print("✅ All tests completed!")
    print("="*70)
