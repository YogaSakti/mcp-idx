#!/usr/bin/env python3
"""Test Volatility Analysis tool with real Indonesian stocks."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.volatility_analysis import get_volatility_analysis


async def test_volatility_analysis():
    """Test volatility analysis with BBCA, BBRI, TLKM."""

    test_tickers = ["BBCA.JK", "BBRI.JK", "TLKM.JK"]

    for ticker in test_tickers:
        print(f"\n{'='*70}")
        print(f"Testing Volatility Analysis: {ticker}")
        print(f"{'='*70}")

        try:
            result = await get_volatility_analysis({
                "ticker": ticker,
                "period": "3mo"
            })

            if "error" in result:
                print(f"❌ Error: {result['error']}")
                continue

            print(f"\n📊 {ticker}")
            print(f"   Current Price: Rp {result['current_price']:,.2f}")
            print(f"   Period: {result['period']}")

            # Historical volatility
            if "historical_volatility" in result:
                print(f"\n📈 Historical Volatility:")
                hv = result['historical_volatility']
                for period, data in hv.items():
                    if isinstance(data, dict):
                        print(f"   {period.upper()}:")
                        print(f"      Value: {data['value']:.2f}%")
                        print(f"      Level: {data['level'].upper()}")
                    else:
                        print(f"   {period.upper()}: {data:.2f}%")

            # Price ranges
            if "price_ranges" in result:
                print(f"\n📊 Price Ranges:")
                pr = result['price_ranges']
                for period, data in pr.items():
                    if isinstance(data, dict):
                        print(f"   {period.upper()}:")
                        print(f"      High: Rp {data['high']:,.2f}")
                        print(f"      Low: Rp {data['low']:,.2f}")
                        print(f"      Range: {data['range']:.2f}%")

            # ATR (Average True Range)
            if "atr" in result:
                print(f"\n📏 Average True Range (ATR):")
                atr = result['atr']
                if isinstance(atr, dict):
                    print(f"   ATR Value: Rp {atr['value']:,.2f}")
                    print(f"   ATR %: {atr['percentage']:.2f}%")
                    print(f"   Level: {atr['level'].upper()}")
                else:
                    print(f"   ATR: {atr:.2f}")

            # Bollinger Bands
            if "bollinger_bands" in result:
                print(f"\n📊 Bollinger Bands:")
                bb = result['bollinger_bands']
                print(f"   Upper: Rp {bb['upper']:,.2f}")
                print(f"   Middle: Rp {bb['middle']:,.2f}")
                print(f"   Lower: Rp {bb['lower']:,.2f}")
                print(f"   Width: {bb['width']:.2f}%")
                print(f"   Position: {bb['position'].upper()}")

            # Volatility classification
            if "volatility_classification" in result:
                print(f"\n🎯 Volatility Classification:")
                vc = result['volatility_classification']
                print(f"   Level: {vc['level'].upper()}")
                print(f"   Risk: {vc['risk'].upper()}")
                print(f"   Description: {vc['description']}")

            # Insights
            if "insights" in result and result["insights"]:
                print(f"\n💡 Trading Insights:")
                for insight in result["insights"]:
                    print(f"   {insight}")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_volatility_analysis())
