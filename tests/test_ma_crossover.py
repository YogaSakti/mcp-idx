#!/usr/bin/env python3
"""Test MA Crossover detection with real Indonesian stocks."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.ma_crossover import get_ma_crossovers


async def test_ma_crossovers():
    """Test MA crossovers with BBCA, BBRI, TLKM."""

    test_tickers = ["BBCA.JK", "BBRI.JK", "TLKM.JK"]

    for ticker in test_tickers:
        print(f"\n{'='*70}")
        print(f"Testing MA Crossovers: {ticker}")
        print(f"{'='*70}")

        try:
            result = await get_ma_crossovers({
                "ticker": ticker,
                "period": "1y",  # Need enough data for SMA 200
                "lookback_days": 60  # Look back 60 days
            })

            if "error" in result:
                print(f"❌ Error: {result['error']}")
                continue

            print(f"\n📊 Current Price: Rp {result['current_price']:,.2f}")

            # Current MA values
            if "current_mas" in result and result["current_mas"]:
                print(f"\n📈 Current Moving Averages:")
                mas = result["current_mas"]
                if "sma_50" in mas:
                    print(f"   SMA 50:  Rp {mas['sma_50']:,.2f}")
                if "sma_200" in mas:
                    print(f"   SMA 200: Rp {mas['sma_200']:,.2f}")
                if "ema_12" in mas:
                    print(f"   EMA 12:  Rp {mas['ema_12']:,.2f}")
                if "ema_26" in mas:
                    print(f"   EMA 26:  Rp {mas['ema_26']:,.2f}")

            # Current alignment
            if "current_alignment" in result and result["current_alignment"]:
                print(f"\n🎯 Current Alignment:")
                align = result["current_alignment"]
                if "sma_50_200" in align:
                    status = "🟢 BULLISH" if align["sma_50_200"] == "bullish" else "🔴 BEARISH"
                    print(f"   SMA 50/200: {status}")
                if "ema_12_26" in align:
                    status = "🟢 BULLISH" if align["ema_12_26"] == "bullish" else "🔴 BEARISH"
                    print(f"   EMA 12/26:  {status}")

            # Detected crossovers
            if "crossovers" in result and result["crossovers"]:
                print(f"\n⚡ Detected Crossovers (last {result['lookback_days']} days):")

                if "sma_50_200" in result["crossovers"]:
                    print(f"\n   📍 SMA 50/200 Crossovers:")
                    for cross in result["crossovers"]["sma_50_200"]:
                        signal_icon = "🟢" if cross["signal"] == "bullish" else "🔴"
                        cross_type = "GOLDEN CROSS" if cross["type"] == "golden_cross" else "DEATH CROSS"
                        print(f"      {signal_icon} {cross_type} on {cross['date']}")
                        print(f"         SMA 50: Rp {cross['fast_ma_value']:,.2f}")
                        print(f"         SMA 200: Rp {cross['slow_ma_value']:,.2f}")

                if "ema_12_26" in result["crossovers"]:
                    print(f"\n   📍 EMA 12/26 Crossovers:")
                    for cross in result["crossovers"]["ema_12_26"]:
                        signal_icon = "🟢" if cross["signal"] == "bullish" else "🔴"
                        print(f"      {signal_icon} {cross['type'].upper()} on {cross['date']}")
                        print(f"         EMA 12: Rp {cross['fast_ma_value']:,.2f}")
                        print(f"         EMA 26: Rp {cross['slow_ma_value']:,.2f}")
            else:
                print(f"\n⚪ No crossovers detected in the lookback period")

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
    asyncio.run(test_ma_crossovers())
