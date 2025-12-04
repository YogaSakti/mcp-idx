"""Test Fibonacci retracement levels with real IDX stock data."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.fibonacci import get_fibonacci_levels


async def test_fibonacci_levels():
    """Test Fibonacci with real stock data."""
    test_stocks = ["BBCA", "BBRI", "TLKM"]

    print("=" * 70)
    print("Testing Fibonacci Retracement & Extension Levels")
    print("=" * 70)
    print()

    for ticker in test_stocks:
        print(f"\n📊 Testing {ticker}.JK")
        print("-" * 70)

        try:
            # Test Fibonacci levels with auto trend detection
            result = await get_fibonacci_levels({
                "ticker": ticker,
                "period": "3mo",
                "trend": "auto"
            })

            if "error" in result:
                print(f"❌ Error: {result.get('message')}")
                continue

            # Display results
            print(f"Ticker: {result['ticker']}")
            print(f"Period: {result['period']}")
            print(f"Current Price: Rp {result['current_price']:,.0f}")
            print(f"Trend: {result['trend'].upper()}")
            print()

            # Swing Points
            print("📍 Swing Points:")
            print(f"  Swing High: Rp {result['swing_high']:,.0f}")
            print(f"  Swing Low:  Rp {result['swing_low']:,.0f}")
            print(f"  Range:      Rp {result['price_range']:,.0f}")
            print()

            # Retracement Levels
            print("📉 Fibonacci Retracement Levels:")
            for level, price in result['retracement_levels'].items():
                marker = " 👈 CURRENT" if abs(price - result['current_price']) < result['price_range'] * 0.05 else ""
                print(f"  {level:6} → Rp {price:>8,.0f}{marker}")
            print()

            # Extension Levels
            print("📈 Fibonacci Extension Levels:")
            for level, price in result['extension_levels'].items():
                print(f"  {level:6} → Rp {price:>8,.0f}")
            print()

            # Support/Resistance Analysis
            print("🎯 Support & Resistance Analysis:")
            print(f"  Nearest Support:    {result['nearest_support']['level']:6} at Rp {result['nearest_support']['price']:,.0f}")
            print(f"  Nearest Resistance: {result['nearest_resistance']['level']:6} at Rp {result['nearest_resistance']['price']:,.0f}")
            print(f"  Current Position: {result['current_position']}")
            print()

            # Risk/Reward
            if result['risk_reward_ratio'] > 0:
                print(f"⚖️  Risk/Reward Ratio: {result['risk_reward_ratio']}")
                if result['risk_reward_ratio'] >= 2:
                    print(f"  ✅ Good R/R ratio (>= 2:1)")
                elif result['risk_reward_ratio'] >= 1:
                    print(f"  ⚠️  Acceptable R/R ratio (>= 1:1)")
                else:
                    print(f"  ❌ Poor R/R ratio (< 1:1)")
            print()

            # Trading Insights
            print("💡 Trading Insights:")
            if result['trend'] == "uptrend":
                print(f"  • Look for buying opportunities at support levels")
                print(f"  • Target: {result['nearest_resistance']['level']} (Rp {result['nearest_resistance']['price']:,.0f})")
                print(f"  • Stop Loss: Below {result['nearest_support']['level']} (Rp {result['nearest_support']['price']:,.0f})")
            else:
                print(f"  • Look for selling opportunities at resistance levels")
                print(f"  • Target: {result['nearest_support']['level']} (Rp {result['nearest_support']['price']:,.0f})")
                print(f"  • Stop Loss: Above {result['nearest_resistance']['level']} (Rp {result['nearest_resistance']['price']:,.0f})")

        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print("✅ Fibonacci Testing Complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_fibonacci_levels())
