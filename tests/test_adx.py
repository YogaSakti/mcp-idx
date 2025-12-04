"""Test ADX indicator with real IDX stock data."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.indicators import get_technical_indicators


async def test_adx_indicator():
    """Test ADX with real stock data."""
    test_stocks = ["BBCA", "BBRI", "TLKM"]

    print("=" * 60)
    print("Testing ADX Indicator with Real IDX Stock Data")
    print("=" * 60)
    print()

    for ticker in test_stocks:
        print(f"\n📊 Testing {ticker}.JK")
        print("-" * 60)

        try:
            # Test ADX indicator
            result = await get_technical_indicators({
                "ticker": ticker,
                "indicators": ["adx", "rsi", "macd"],
                "period": "3mo"
            })

            if "error" in result:
                print(f"❌ Error: {result.get('message')}")
                continue

            # Display results
            print(f"Ticker: {result['ticker']}")
            print(f"Current Price: {result['current_price']}")
            print()

            # ADX
            if "adx" in result.get("indicators", {}):
                adx = result["indicators"]["adx"]
                print("ADX Indicator:")
                print(f"  ADX Value: {adx['value']}")
                print(f"  +DI: {adx['plus_di']}")
                print(f"  -DI: {adx['minus_di']}")
                print(f"  Trend Strength: {adx['trend_strength']}")
                print(f"  Trend Direction: {adx['trend_direction']}")
                print()

                # Interpretation
                if adx['trend_strength'] == 'strong':
                    if adx['trend_direction'] == 'bullish':
                        print(f"  ✅ Interpretation: Strong Bullish Trend")
                    else:
                        print(f"  ⚠️  Interpretation: Strong Bearish Trend")
                elif adx['trend_strength'] == 'developing':
                    print(f"  📈 Interpretation: Developing {adx['trend_direction'].capitalize()} Trend")
                else:
                    print(f"  ⏸️  Interpretation: Weak/No Clear Trend (Sideways)")
            else:
                print("❌ ADX not calculated")

            # Compare with RSI for confirmation
            if "rsi_14" in result.get("indicators", {}):
                rsi = result["indicators"]["rsi_14"]
                print(f"\nRSI (for confirmation): {rsi['value']} - {rsi['interpretation']}")

            # Compare with MACD
            if "macd" in result.get("indicators", {}):
                macd = result["indicators"]["macd"]
                print(f"MACD: {macd['interpretation']}")

            print()

        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("✅ ADX Testing Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_adx_indicator())
