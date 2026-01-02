"""Test intraday tools - VWAP, Pivot Points, Gap Analysis."""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.tools.intraday import get_vwap, get_pivot_points, get_gap_analysis


async def test_vwap():
    """Test VWAP calculation."""
    print("\n" + "="*60)
    print("📊 TEST: VWAP (Volume Weighted Average Price)")
    print("="*60)
    
    result = await get_vwap({
        "ticker": "WIFI",
        "period": "5d",
        "include_bands": True
    })
    
    if "error" in result:
        print(f"❌ Error: {result.get('message', result)}")
        return False
    
    print(f"✅ Ticker: {result['ticker']}")
    print(f"   Current Price: Rp {result['current_price']:,.0f}")
    print(f"   VWAP: Rp {result['vwap']:,.0f}")
    print(f"   Deviation: {result['deviation_percent']:+.2f}%")
    print(f"   Position: {result['position']}")
    print(f"   Signal: {result['signal']}")
    
    if result.get('bands'):
        print(f"\n   VWAP Bands:")
        for key, val in result['bands'].items():
            print(f"   - {key}: Rp {val:,.0f}")
    
    print(f"\n   Trading Guidance:")
    print(f"   - Bias: {result['trading_guidance']['bias']}")
    print(f"   - Entry Zone: {result['trading_guidance']['entry_zone']}")
    
    return True


async def test_pivot_points():
    """Test Pivot Points calculation."""
    print("\n" + "="*60)
    print("📊 TEST: PIVOT POINTS")
    print("="*60)
    
    result = await get_pivot_points({
        "ticker": "WIFI",
        "pivot_type": "all"
    })
    
    if "error" in result:
        print(f"❌ Error: {result.get('message', result)}")
        return False
    
    print(f"✅ Ticker: {result['ticker']}")
    print(f"   Current Price: Rp {result['current_price']:,.0f}")
    print(f"   Position: {result['position']}")
    print(f"   Bias: {result['bias']}")
    print(f"   Signal: {result['signal']}")
    
    # Print all pivot types
    for pivot_type, levels in result['pivots'].items():
        print(f"\n   {pivot_type.upper()} PIVOTS:")
        for level, price in sorted(levels.items(), key=lambda x: x[1], reverse=True):
            marker = " <<<" if level == "PP" else ""
            print(f"   - {level}: Rp {price:,.0f}{marker}")
    
    print(f"\n   Nearest Support: {result['nearest_support']}")
    print(f"   Nearest Resistance: {result['nearest_resistance']}")
    
    print(f"\n   Trading Guidance:")
    print(f"   - {result['trading_guidance']['guidance']}")
    print(f"   - Risk Level: {result['trading_guidance']['risk_level']}")
    
    return True


async def test_gap_analysis():
    """Test Gap Analysis."""
    print("\n" + "="*60)
    print("📊 TEST: GAP ANALYSIS")
    print("="*60)
    
    result = await get_gap_analysis({
        "ticker": "WIFI"
    })
    
    if "error" in result:
        print(f"❌ Error: {result.get('message', result)}")
        return False
    
    print(f"✅ Ticker: {result['ticker']}")
    print(f"   Current Price: Rp {result['current_price']:,.0f}")
    
    gap = result['gap_analysis']
    print(f"\n   Gap Analysis:")
    print(f"   - Type: {gap['gap_type']}")
    print(f"   - Description: {gap['gap_description']}")
    print(f"   - Gap Size: Rp {gap['gap_size']:,.0f} ({gap['gap_percent']:+.2f}%)")
    print(f"   - Previous Close: Rp {gap['previous_close']:,.0f}")
    print(f"   - Today Open: Rp {gap['today_open']:,.0f}")
    
    fill = result['gap_fill_status']
    print(f"\n   Gap Fill Status:")
    print(f"   - Is Filled: {'✅ Yes' if fill['is_filled'] else '❌ No'}")
    print(f"   - Fill Level: Rp {fill['fill_level']:,.0f}")
    print(f"   - Fill Progress: {fill['fill_progress_percent']:.1f}%")
    
    print(f"\n   True Gap: {result['true_gap']['description']}")
    print(f"\n   Trading Implication: {result['trading_implication']}")
    if result['strategy']:
        print(f"   Strategy: {result['strategy']}")
    
    return True


async def test_multiple_tickers():
    """Test with multiple tickers."""
    print("\n" + "="*60)
    print("📊 TEST: MULTIPLE TICKERS")
    print("="*60)
    
    tickers = ["BBCA", "BBRI", "TLKM"]
    
    for ticker in tickers:
        print(f"\n--- {ticker} ---")
        
        # VWAP
        vwap_result = await get_vwap({"ticker": ticker, "period": "5d"})
        if "error" not in vwap_result:
            print(f"VWAP: Rp {vwap_result['vwap']:,.0f} | Position: {vwap_result['position']}")
        
        # Pivot
        pivot_result = await get_pivot_points({"ticker": ticker, "pivot_type": "standard"})
        if "error" not in pivot_result:
            pp = pivot_result['primary_levels'].get('PP', 0)
            print(f"Pivot: Rp {pp:,.0f} | Bias: {pivot_result['bias']}")
        
        # Gap
        gap_result = await get_gap_analysis({"ticker": ticker})
        if "error" not in gap_result:
            gap = gap_result['gap_analysis']
            print(f"Gap: {gap['gap_type']} ({gap['gap_percent']:+.2f}%)")
    
    return True


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("🧪 INTRADAY TOOLS TEST SUITE")
    print("="*60)
    
    tests = [
        ("VWAP", test_vwap),
        ("Pivot Points", test_pivot_points),
        ("Gap Analysis", test_gap_analysis),
        ("Multiple Tickers", test_multiple_tickers),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = await test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ {name} FAILED with exception: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📋 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status}: {name}")
    
    print(f"\n   Total: {passed}/{total} tests passed")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())

