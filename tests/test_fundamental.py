#!/usr/bin/env python3
"""
Test Advanced Fundamental Analysis Tools
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.fundamental import (
    analyze_financial_statements,
    analyze_earnings_growth,
    analyze_analyst_ratings,
    analyze_dividend_history
)


def print_financial_statements(ticker: str):
    """Test financial statements analysis"""
    print("=" * 60)
    print(f"FINANCIAL STATEMENTS ANALYSIS: {ticker}")
    print("=" * 60)
    
    result = analyze_financial_statements(ticker)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return
    
    print(f"\n📊 Ticker: {result['ticker']}")
    print(f"📅 Last Updated: {result['last_updated']}")
    
    if 'income_statement' in result:
        print(f"\n📈 INCOME STATEMENT:")
        inc = result['income_statement']
        print(f"   Period: {inc['period']}")
        print(f"   Revenue: Rp {inc['total_revenue']:,.0f}")
        print(f"   Gross Profit: Rp {inc['gross_profit']:,.0f}")
        print(f"   Operating Income: Rp {inc['operating_income']:,.0f}")
        print(f"   Net Income: Rp {inc['net_income']:,.0f}")
        print(f"   EBITDA: Rp {inc['ebitda']:,.0f}")
        if 'gross_margin' in inc:
            print(f"\n   Margins:")
            print(f"   • Gross Margin: {inc['gross_margin']:.2f}%")
            print(f"   • Operating Margin: {inc['operating_margin']:.2f}%")
            print(f"   • Net Margin: {inc['net_margin']:.2f}%")
    
    if 'balance_sheet' in result:
        print(f"\n💰 BALANCE SHEET:")
        bal = result['balance_sheet']
        print(f"   Period: {bal['period']}")
        print(f"   Total Assets: Rp {bal['total_assets']:,.0f}")
        print(f"   Total Liabilities: Rp {bal['total_liabilities']:,.0f}")
        print(f"   Total Equity: Rp {bal['total_equity']:,.0f}")
        print(f"   Cash: Rp {bal['cash']:,.0f}")
        if 'current_ratio' in bal:
            print(f"\n   Ratios:")
            print(f"   • Current Ratio: {bal['current_ratio']:.2f}x")
            print(f"   • Debt to Assets: {bal['debt_to_assets']:.2f}%")
            print(f"   • Debt to Equity: {bal['debt_to_equity']:.2f}%")
    
    if 'cash_flow' in result:
        print(f"\n💸 CASH FLOW:")
        cf = result['cash_flow']
        print(f"   Period: {cf['period']}")
        print(f"   Operating Cash Flow: Rp {cf['operating_cash_flow']:,.0f}")
        print(f"   Investing Cash Flow: Rp {cf['investing_cash_flow']:,.0f}")
        print(f"   Financing Cash Flow: Rp {cf['financing_cash_flow']:,.0f}")
        print(f"   Free Cash Flow: Rp {cf['free_cash_flow']:,.0f}")
    
    if 'financial_health' in result:
        print(f"\n🏥 FINANCIAL HEALTH:")
        health = result['financial_health']
        print(f"   Score: {health['score']}/100")
        print(f"   Rating: {health['rating']}")
        print(f"   Issues: {', '.join(health['issues'])}")
    
    print()


def print_earnings_growth(ticker: str):
    """Test earnings growth analysis"""
    print("=" * 60)
    print(f"EARNINGS GROWTH ANALYSIS: {ticker}")
    print("=" * 60)
    
    result = analyze_earnings_growth(ticker)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return
    
    print(f"\n📊 Ticker: {result['ticker']}")
    
    if 'historical_earnings' in result:
        print(f"\n📈 HISTORICAL EARNINGS:")
        for period in result['historical_earnings']:
            print(f"   {period['period']}:")
            print(f"      Revenue: Rp {period['revenue']:,.0f}")
            print(f"      Net Income: Rp {period['net_income']:,.0f}")
            print(f"      EBITDA: Rp {period['ebitda']:,.0f}")
    
    if 'yoy_growth' in result:
        print(f"\n📊 YEAR-OVER-YEAR GROWTH:")
        growth = result['yoy_growth']
        print(f"   Revenue Growth: {growth.get('revenue_growth', 0):+.2f}%")
        print(f"   Earnings Growth: {growth.get('earnings_growth', 0):+.2f}%")
        print(f"   EBITDA Growth: {growth.get('ebitda_growth', 0):+.2f}%")
    
    if 'cagr' in result:
        print(f"\n📈 CAGR ({len(result['historical_earnings'])-1} years):")
        cagr = result['cagr']
        if 'revenue_cagr' in cagr:
            print(f"   Revenue CAGR: {cagr['revenue_cagr']:+.2f}%")
        if 'earnings_cagr' in cagr:
            print(f"   Earnings CAGR: {cagr['earnings_cagr']:+.2f}%")
    
    if 'growth_rating' in result:
        print(f"\n⭐ Growth Rating: {result['growth_rating']}")
    
    print()


def print_analyst_ratings(ticker: str):
    """Test analyst ratings analysis"""
    print("=" * 60)
    print(f"ANALYST RATINGS: {ticker}")
    print("=" * 60)
    
    result = analyze_analyst_ratings(ticker)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return
    
    print(f"\n📊 Ticker: {result['ticker']}")
    print(f"📅 Analysis Date: {result['analysis_date']}")
    
    if 'analyst_ratings' in result:
        print(f"\n👥 ANALYST RECOMMENDATIONS:")
        ratings = result['analyst_ratings']
        print(f"   Total Analysts: {ratings['total_analysts']}")
        print(f"   Strong Buy: {ratings['strong_buy']}")
        print(f"   Buy: {ratings['buy']}")
        print(f"   Hold: {ratings['hold']}")
        print(f"   Sell: {ratings['sell']}")
        print(f"   Strong Sell: {ratings['strong_sell']}")
        print(f"\n   Consensus: {ratings['consensus']}")
    
    if 'earnings_estimates' in result:
        print(f"\n💰 EARNINGS ESTIMATES:")
        if 'current_quarter' in result['earnings_estimates']:
            cq = result['earnings_estimates']['current_quarter']
            print(f"   Current Quarter ({cq['period']}):")
            print(f"      Avg Estimate: Rp {cq['avg_estimate']:,.2f}")
            print(f"      Range: Rp {cq['low_estimate']:,.2f} - Rp {cq['high_estimate']:,.2f}")
            print(f"      YoY Growth: {cq['growth']:+.2f}%")
    
    if 'revenue_estimates' in result:
        print(f"\n📈 REVENUE ESTIMATES:")
        if 'current_quarter' in result['revenue_estimates']:
            cq = result['revenue_estimates']['current_quarter']
            print(f"   Current Quarter ({cq['period']}):")
            print(f"      Avg Estimate: Rp {cq['avg_estimate']:,.0f}")
            print(f"      YoY Growth: {cq['growth']:+.2f}%")
    
    if 'earnings_calendar' in result:
        print(f"\n📅 EARNINGS CALENDAR:")
        cal = result['earnings_calendar']
        print(f"   Next Earnings Date: {cal['earnings_date']}")
        print(f"   Expected EPS: Rp {cal['earnings_avg']:,.2f}")
        print(f"   Expected Revenue: Rp {cal['revenue_avg']:,.0f}")
    
    print()


def print_dividend_history(ticker: str):
    """Test dividend history analysis"""
    print("=" * 60)
    print(f"DIVIDEND HISTORY: {ticker}")
    print("=" * 60)
    
    result = analyze_dividend_history(ticker)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return
    
    print(f"\n📊 Ticker: {result['ticker']}")
    
    if not result.get('has_dividend', False):
        print(f"\n❌ {result.get('message', 'No dividend data')}")
        return
    
    if 'dividend_history' in result:
        print(f"\n💰 RECENT DIVIDENDS:")
        for div in result['dividend_history']:
            print(f"   {div['date']}: Rp {div['amount']:,.2f}")
    
    if 'dividend_stats' in result:
        print(f"\n📊 DIVIDEND STATISTICS:")
        stats = result['dividend_stats']
        print(f"   Latest Dividend: Rp {stats['latest_dividend']:,.2f}")
        print(f"   Latest Date: {stats['latest_date']}")
        print(f"   Annual Dividend: Rp {stats['annual_dividend']:,.2f}")
        if 'dividend_yield' in stats:
            print(f"   Dividend Yield: {stats['dividend_yield']:.2f}%")
        if 'yoy_growth' in stats:
            print(f"   YoY Growth: {stats['yoy_growth']:+.2f}%")
        print(f"   Years Paying: {stats['years_paying']}")
        print(f"   Consistency: {stats['consistency']}")
    
    if 'dividend_rating' in result:
        print(f"\n⭐ Dividend Rating: {result['dividend_rating']}")
    
    print()


if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "BBRI"
    
    print("\n🔍 COMPLETE FUNDAMENTAL ANALYSIS\n")
    
    # Test all analyses
    print_financial_statements(ticker)
    print_earnings_growth(ticker)
    print_analyst_ratings(ticker)
    print_dividend_history(ticker)
    
    print("=" * 60)
    print("✅ Analysis Complete!")
    print("=" * 60)
