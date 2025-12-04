#!/usr/bin/env python3
"""Test Financial Ratios tool with real Indonesian stocks."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.financial_ratios import get_financial_ratios


async def test_financial_ratios():
    """Test financial ratios with BBCA, BBRI, TLKM."""

    test_tickers = ["BBCA.JK", "BBRI.JK", "TLKM.JK"]

    for ticker in test_tickers:
        print(f"\n{'='*70}")
        print(f"Testing Financial Ratios: {ticker}")
        print(f"{'='*70}")

        try:
            result = await get_financial_ratios({"ticker": ticker})

            if "error" in result:
                print(f"❌ Error: {result['error']}")
                continue

            print(f"\n📊 {result.get('name', ticker)}")
            print(f"   Sector: {result.get('sector', 'N/A')}")
            print(f"   Industry: {result.get('industry', 'N/A')}")
            print(f"   Current Price: Rp {result['current_price']:,.2f}")
            if result.get('market_cap'):
                print(f"   Market Cap: Rp {result['market_cap']:,.0f}")
            if result.get('financial_score'):
                print(f"   Financial Score: {result['financial_score']}/100")

            # Summary
            if "summary" in result:
                summary = result["summary"]

                print(f"\n💰 Valuation Metrics:")
                val = summary.get("valuation", {})
                if val.get("pe_ratio"):
                    print(f"   P/E Ratio: {val['pe_ratio']:.2f}")
                if val.get("pb_ratio"):
                    print(f"   P/B Ratio: {val['pb_ratio']:.2f}")
                if val.get("ps_ratio"):
                    print(f"   P/S Ratio: {val['ps_ratio']:.2f}")

                print(f"\n📈 Profitability Metrics:")
                prof = summary.get("profitability", {})
                if prof.get("roe"):
                    print(f"   ROE: {prof['roe']:.2f}%")
                if prof.get("roa"):
                    print(f"   ROA: {prof['roa']:.2f}%")
                if prof.get("profit_margin"):
                    print(f"   Profit Margin: {prof['profit_margin']:.2f}%")

                print(f"\n🏦 Leverage & Liquidity:")
                lev = summary.get("leverage", {})
                liq = summary.get("liquidity", {})
                if lev.get("debt_to_equity"):
                    print(f"   Debt-to-Equity: {lev['debt_to_equity']:.2f}")
                if liq.get("current_ratio"):
                    print(f"   Current Ratio: {liq['current_ratio']:.2f}")
                if liq.get("quick_ratio"):
                    print(f"   Quick Ratio: {liq['quick_ratio']:.2f}")

                print(f"\n💵 Dividend Metrics:")
                div = summary.get("dividend", {})
                if div.get("dividend_yield"):
                    print(f"   Dividend Yield: {div['dividend_yield']:.2f}%")
                if div.get("payout_ratio"):
                    print(f"   Payout Ratio: {div['payout_ratio']:.2f}%")

                print(f"\n📊 Growth Metrics:")
                growth = summary.get("growth", {})
                if growth.get("earnings_growth"):
                    print(f"   Earnings Growth: {growth['earnings_growth']:.2f}%")
                if growth.get("revenue_growth"):
                    print(f"   Revenue Growth: {growth['revenue_growth']:.2f}%")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_financial_ratios())
