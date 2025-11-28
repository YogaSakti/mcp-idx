#!/usr/bin/env python3
"""Test Volume Analysis tool with real Indonesian stocks."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.tools.volume_analysis import get_volume_analysis


async def test_volume_analysis():
    """Test volume analysis with BBCA, BBRI, TLKM."""

    test_tickers = ["BBCA.JK", "BBRI.JK", "TLKM.JK"]

    for ticker in test_tickers:
        print(f"\n{'='*70}")
        print(f"Testing Volume Analysis: {ticker}")
        print(f"{'='*70}")

        try:
            result = await get_volume_analysis({
                "ticker": ticker,
                "period": "3mo"
            })

            if "error" in result:
                print(f"❌ Error: {result['error']}")
                continue

            print(f"\n📊 {ticker}")
            print(f"   Current Price: Rp {result['current_price']:,.2f}")
            print(f"   Period: {result['period']}")

            # Current & previous volume
            if "current_volume" in result:
                print(f"\n📦 Current Volume:")
                print(f"   Current: {result['current_volume']:,}")
            if "previous_volume" in result:
                print(f"   Previous: {result['previous_volume']:,}")

            # Average volumes
            if "averages" in result:
                print(f"\n📊 Average Volumes:")
                avg = result['averages']
                for period, value in avg.items():
                    print(f"   {period.upper()}: {value:,}")

            # Volume ratios
            if "volume_ratios" in result:
                print(f"\n📊 Volume Ratios (Current vs Average):")
                ratios = result['volume_ratios']
                for period, ratio in ratios.items():
                    status = "🔥 HIGH" if ratio >= 2.0 else "⬆️ ABOVE AVG" if ratio >= 1.2 else "➡️ NORMAL" if ratio >= 0.8 else "⬇️ LOW"
                    print(f"   {period.replace('vs_', '').replace('_avg', '').upper()}: {ratio:.2f}x {status}")

            # Volume spikes
            if "spike_detection" in result:
                print(f"\n🔥 Volume Spike Detection:")
                spike = result['spike_detection']
                print(f"   7D Spike: {spike.get('is_spike_7d', False)}")
                print(f"   30D Spike: {spike.get('is_spike_30d', False)}")
                print(f"   90D Spike: {spike.get('is_spike_90d', False)}")
                print(f"   Severity: {spike['severity'].upper()}")

            # Volume trend
            if "trend" in result:
                print(f"\n📈 Volume Trend:")
                trend = result['trend']
                for period, direction in trend.items():
                    trend_icon = "📈" if direction == "increasing" else "📉" if direction == "decreasing" else "➡️"
                    print(f"   {period.upper()}: {trend_icon} {direction.upper()}")

            # Volume-price correlation
            if "volume_price_correlation" in result:
                corr = result['volume_price_correlation']
                print(f"\n🔗 Volume-Price Correlation:")
                print(f"   Correlation: {corr['correlation']:.3f}")
                print(f"   Interpretation: {corr['interpretation']}")

            # Statistics
            if "statistics" in result:
                print(f"\n📊 Statistics:")
                stats = result['statistics']
                print(f"   Max Volume: {stats.get('max_volume', 0):,}")
                print(f"   Min Volume: {stats.get('min_volume', 0):,}")
                print(f"   Std Dev: {stats.get('std_deviation', 0):,}")

            # Unusual volume
            if "unusual_volume" in result:
                print(f"\n⚠️ Unusual Volume Detection:")
                unusual = result['unusual_volume']
                print(f"   Is Unusual: {unusual['is_unusual']}")
                print(f"   Type: {unusual['type'].upper()}")
                print(f"   Z-Score: {unusual['z_score']:.2f}")

            # Summary
            if "summary" in result:
                print(f"\n📝 Summary:")
                summary = result['summary']
                print(f"   Current Status: {summary.get('current_volume_status', 'unknown').upper()}")
                print(f"   Trend: {summary.get('trend', 'unknown').upper()}")
                print(f"   Correlation: {summary.get('correlation_strength', 'unknown').upper()}")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_volume_analysis())
