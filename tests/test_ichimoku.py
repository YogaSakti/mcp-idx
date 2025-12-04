#!/usr/bin/env python3
"""Test Ichimoku Cloud implementation with real Indonesian stocks."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.indicators import get_technical_indicators


async def test_ichimoku():
    """Test Ichimoku with BBCA, BBRI, TLKM."""

    test_tickers = ["BBCA.JK", "BBRI.JK", "TLKM.JK"]

    for ticker in test_tickers:
        print(f"\n{'='*60}")
        print(f"Testing {ticker}")
        print(f"{'='*60}")

        try:
            result = await get_technical_indicators({
                "ticker": ticker,
                "indicators": ["ichimoku"],
                "period": "6mo"  # Need enough data for Ichimoku (52 periods)
            })

            if "indicators" in result and "ichimoku" in result["indicators"]:
                ich = result["indicators"]["ichimoku"]
                print(f"\n✅ Ichimoku Cloud Data:")
                print(f"   Tenkan-sen (9):      Rp {ich['tenkan_sen']:,.2f}")
                print(f"   Kijun-sen (26):      Rp {ich['kijun_sen']:,.2f}")
                print(f"   Senkou Span A:       Rp {ich['senkou_span_a']:,.2f}")
                print(f"   Senkou Span B:       Rp {ich['senkou_span_b']:,.2f}")
                print(f"\n   Cloud Color:         {ich['cloud_color'].upper()}")
                print(f"   Price vs Cloud:      {ich['price_vs_cloud'].upper()}")
                print(f"   TK Cross:            {ich['tk_cross'].upper()}")
                print(f"   Overall Signal:      {ich['signal'].upper()}")

                # Interpretation
                print(f"\n📊 Interpretation:")
                if ich['signal'] == 'strong_bullish':
                    print("   🟢 STRONG BULLISH - All indicators aligned bullish")
                elif ich['signal'] == 'strong_bearish':
                    print("   🔴 STRONG BEARISH - All indicators aligned bearish")
                elif ich['signal'] == 'bullish':
                    print("   🟢 BULLISH - Price above cloud")
                elif ich['signal'] == 'bearish':
                    print("   🔴 BEARISH - Price below cloud")
                else:
                    print("   🟡 NEUTRAL - Mixed signals or inside cloud")

                # Cloud interpretation
                if ich['cloud_color'] == 'bullish':
                    print("   ☁️  Bullish Cloud (Span A > Span B)")
                else:
                    print("   ☁️  Bearish Cloud (Span A < Span B)")

            else:
                print(f"❌ No Ichimoku data returned")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_ichimoku())
