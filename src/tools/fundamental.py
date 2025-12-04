"""
Advanced Fundamental Analysis Tools
Analisis laporan keuangan, earnings, analyst ratings, dan dividend history
"""

from ..utils.yahoo import YahooFinanceClient
from ..utils.validators import validate_ticker
from ..utils.helpers import format_ticker
from mcp.types import Tool
import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import Dict, Any

# Initialize API
yahoo_api = YahooFinanceClient()


def analyze_financial_statements(ticker: str) -> dict:
    """
    Analisis lengkap laporan keuangan (Income Statement, Balance Sheet, Cash Flow).
    Termasuk valuation metrics (PE Ratio, PBV, dll).
    
    Args:
        ticker: Stock ticker
        
    Returns:
        Dictionary dengan analisis financial statements
    """
    ticker = validate_ticker(ticker)
    ticker_jk = format_ticker(ticker)
    
    try:
        stock = yf.Ticker(ticker_jk)
        info = stock.info
        
        # Get financial statements
        income_stmt = stock.income_stmt
        balance_sheet = stock.balance_sheet
        cash_flow = stock.cash_flow
        
        if income_stmt is None or income_stmt.empty:
            return {"error": "Financial statements not available"}
        
        result = {
            "ticker": ticker.replace('.JK', ''),
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
        }
        
        # === VALUATION METRICS from Info ===
        current_price = info.get('currentPrice', 0) or info.get('regularMarketPrice', 0)
        
        valuation = {
            "current_price": current_price,
            "market_cap": info.get('marketCap', 0),
            "enterprise_value": info.get('enterpriseValue', 0),
        }
        
        # PE Ratio
        pe_trailing = info.get('trailingPE', None)
        pe_forward = info.get('forwardPE', None)
        valuation['pe_trailing'] = round(pe_trailing, 2) if pe_trailing else None
        valuation['pe_forward'] = round(pe_forward, 2) if pe_forward else None
        
        # PBV (Price to Book Value)
        pbv = info.get('priceToBook', None)
        valuation['pbv'] = round(pbv, 2) if pbv else None
        
        # Other valuation metrics
        ps_ratio = info.get('priceToSalesTrailing12Months', None)
        valuation['ps_ratio'] = round(ps_ratio, 2) if ps_ratio else None
        
        ev_ebitda = info.get('enterpriseToEbitda', None)
        valuation['ev_to_ebitda'] = round(ev_ebitda, 2) if ev_ebitda else None
        
        ev_revenue = info.get('enterpriseToRevenue', None)
        valuation['ev_to_revenue'] = round(ev_revenue, 2) if ev_revenue else None
        
        # PEG Ratio
        peg = info.get('pegRatio', None)
        valuation['peg_ratio'] = round(peg, 2) if peg else None
        
        # Valuation Assessment
        valuation_signals = []
        
        if pe_trailing:
            if pe_trailing < 10:
                valuation_signals.append("🟢 PE rendah (<10) - Potentially undervalued")
            elif pe_trailing < 15:
                valuation_signals.append("🟢 PE wajar (10-15)")
            elif pe_trailing < 25:
                valuation_signals.append("🟡 PE moderate (15-25)")
            else:
                valuation_signals.append("🔴 PE tinggi (>25) - Potentially overvalued")
        
        if pbv:
            if pbv < 1:
                valuation_signals.append("🟢 PBV < 1 - Trading below book value")
            elif pbv < 2:
                valuation_signals.append("🟢 PBV wajar (1-2)")
            elif pbv < 5:
                valuation_signals.append("🟡 PBV moderate (2-5)")
            else:
                valuation_signals.append("🔴 PBV tinggi (>5)")
        
        valuation['assessment'] = valuation_signals if valuation_signals else ["Data tidak tersedia"]
        
        result['valuation'] = valuation
        
        # Parse Income Statement (latest year)
        if not income_stmt.empty:
            latest = income_stmt.columns[0]
            
            income_data = {
                "period": str(latest)[:10],
                "total_revenue": float(income_stmt.loc['Total Revenue', latest]) if 'Total Revenue' in income_stmt.index else 0,
                "gross_profit": float(income_stmt.loc['Gross Profit', latest]) if 'Gross Profit' in income_stmt.index else 0,
                "operating_income": float(income_stmt.loc['Operating Income', latest]) if 'Operating Income' in income_stmt.index else 0,
                "net_income": float(income_stmt.loc['Net Income', latest]) if 'Net Income' in income_stmt.index else 0,
                "ebitda": float(income_stmt.loc['EBITDA', latest]) if 'EBITDA' in income_stmt.index else 0,
            }
            
            # Calculate margins
            revenue = income_data['total_revenue']
            if revenue > 0:
                income_data['gross_margin'] = (income_data['gross_profit'] / revenue) * 100
                income_data['operating_margin'] = (income_data['operating_income'] / revenue) * 100
                income_data['net_margin'] = (income_data['net_income'] / revenue) * 100
            
            result['income_statement'] = income_data
        
        # Parse Balance Sheet (latest quarter)
        if balance_sheet is not None and not balance_sheet.empty:
            latest = balance_sheet.columns[0]
            
            balance_data = {
                "period": str(latest)[:10],
                "total_assets": float(balance_sheet.loc['Total Assets', latest]) if 'Total Assets' in balance_sheet.index else 0,
                "total_liabilities": float(balance_sheet.loc['Total Liabilities Net Minority Interest', latest]) if 'Total Liabilities Net Minority Interest' in balance_sheet.index else 0,
                "total_equity": float(balance_sheet.loc['Total Equity Gross Minority Interest', latest]) if 'Total Equity Gross Minority Interest' in balance_sheet.index else 0,
                "current_assets": float(balance_sheet.loc['Current Assets', latest]) if 'Current Assets' in balance_sheet.index else 0,
                "current_liabilities": float(balance_sheet.loc['Current Liabilities', latest]) if 'Current Liabilities' in balance_sheet.index else 0,
                "cash": float(balance_sheet.loc['Cash And Cash Equivalents', latest]) if 'Cash And Cash Equivalents' in balance_sheet.index else 0,
            }
            
            # Calculate ratios
            if balance_data['total_assets'] > 0:
                balance_data['debt_to_assets'] = (balance_data['total_liabilities'] / balance_data['total_assets']) * 100
            
            if balance_data['total_equity'] > 0:
                balance_data['debt_to_equity'] = (balance_data['total_liabilities'] / balance_data['total_equity']) * 100
            
            if balance_data['current_liabilities'] > 0:
                balance_data['current_ratio'] = balance_data['current_assets'] / balance_data['current_liabilities']
            
            result['balance_sheet'] = balance_data
        
        # Parse Cash Flow (latest year)
        if cash_flow is not None and not cash_flow.empty:
            latest = cash_flow.columns[0]
            
            cashflow_data = {
                "period": str(latest)[:10],
                "operating_cash_flow": float(cash_flow.loc['Operating Cash Flow', latest]) if 'Operating Cash Flow' in cash_flow.index else 0,
                "investing_cash_flow": float(cash_flow.loc['Investing Cash Flow', latest]) if 'Investing Cash Flow' in cash_flow.index else 0,
                "financing_cash_flow": float(cash_flow.loc['Financing Cash Flow', latest]) if 'Financing Cash Flow' in cash_flow.index else 0,
                "free_cash_flow": float(cash_flow.loc['Free Cash Flow', latest]) if 'Free Cash Flow' in cash_flow.index else 0,
            }
            
            result['cash_flow'] = cashflow_data
        
        # Financial Health Score (now out of 100 with more factors)
        score = 0
        max_score = 100
        health_issues = []
        health_positives = []
        
        # 1. Profitability (25 points)
        if 'income_statement' in result:
            net_margin = result['income_statement'].get('net_margin', 0)
            if net_margin > 15:
                score += 25
                health_positives.append("✅ Excellent profit margin (>15%)")
            elif net_margin > 10:
                score += 20
                health_positives.append("✅ Good profit margin (>10%)")
            elif net_margin > 5:
                score += 10
            elif net_margin < 5:
                health_issues.append("⚠️ Low profit margin (<5%)")
        
        # 2. Liquidity (20 points)
        if 'balance_sheet' in result:
            current_ratio = result['balance_sheet'].get('current_ratio', 0)
            if current_ratio > 2:
                score += 20
                health_positives.append("✅ Strong liquidity (CR > 2)")
            elif current_ratio > 1.5:
                score += 15
            elif current_ratio > 1:
                score += 10
            elif current_ratio < 1:
                health_issues.append("🔴 Low liquidity (current ratio < 1)")
        
        # 3. Leverage (20 points)
        if 'balance_sheet' in result:
            dte = result['balance_sheet'].get('debt_to_equity', 0)
            if dte < 50:
                score += 20
                health_positives.append("✅ Low debt (D/E < 50%)")
            elif dte < 100:
                score += 15
            elif dte < 150:
                score += 10
            elif dte > 200:
                health_issues.append("🔴 High debt levels (D/E > 200%)")
        
        # 4. Cash Flow (20 points)
        if 'cash_flow' in result:
            ocf = result['cash_flow'].get('operating_cash_flow', 0)
            fcf = result['cash_flow'].get('free_cash_flow', 0)
            if ocf > 0 and fcf > 0:
                score += 20
                health_positives.append("✅ Positive cash flow")
            elif ocf > 0:
                score += 10
            else:
                health_issues.append("🔴 Negative operating cash flow")
        
        # 5. Valuation (15 points)
        if 'valuation' in result:
            pe = result['valuation'].get('pe_trailing')
            pbv = result['valuation'].get('pbv')
            
            if pe and pe < 15:
                score += 8
            elif pe and pe > 30:
                health_issues.append("⚠️ High PE ratio (>30)")
            
            if pbv and pbv < 2:
                score += 7
            elif pbv and pbv > 5:
                health_issues.append("⚠️ High PBV (>5)")
        
        result['financial_health'] = {
            "score": min(score, max_score),
            "rating": "🟢 Excellent" if score >= 80 else "🟢 Good" if score >= 60 else "🟡 Fair" if score >= 40 else "🔴 Poor",
            "positives": health_positives if health_positives else ["None"],
            "issues": health_issues if health_issues else ["None"]
        }
        
        return result
        
    except Exception as e:
        return {"error": str(e)}


def analyze_earnings_growth(ticker: str) -> dict:
    """
    Analisis pertumbuhan earnings dan revenue.
    
    Args:
        ticker: Stock ticker
        
    Returns:
        Dictionary dengan analisis earnings growth
    """
    ticker = validate_ticker(ticker)
    ticker_jk = format_ticker(ticker)
    
    try:
        stock = yf.Ticker(ticker_jk)
        
        # Get income statement for historical data
        income_stmt = stock.income_stmt
        
        if income_stmt is None or income_stmt.empty or len(income_stmt.columns) < 2:
            return {"error": "Insufficient earnings data"}
        
        result = {
            "ticker": ticker.replace('.JK', ''),
        }
        
        # Get historical earnings (multiple periods)
        periods = []
        for i, col in enumerate(income_stmt.columns[:4]):  # Last 4 years
            period_data = {
                "period": str(col)[:10],
                "revenue": float(income_stmt.loc['Total Revenue', col]) if 'Total Revenue' in income_stmt.index else 0,
                "net_income": float(income_stmt.loc['Net Income', col]) if 'Net Income' in income_stmt.index else 0,
                "ebitda": float(income_stmt.loc['EBITDA', col]) if 'EBITDA' in income_stmt.index else 0,
            }
            periods.append(period_data)
        
        result['historical_earnings'] = periods
        
        # Calculate growth rates (YoY)
        if len(periods) >= 2:
            latest = periods[0]
            previous = periods[1]
            
            growth = {}
            
            if previous['revenue'] > 0:
                growth['revenue_growth'] = ((latest['revenue'] - previous['revenue']) / previous['revenue']) * 100
            
            if previous['net_income'] > 0:
                growth['earnings_growth'] = ((latest['net_income'] - previous['net_income']) / previous['net_income']) * 100
            
            if previous['ebitda'] > 0:
                growth['ebitda_growth'] = ((latest['ebitda'] - previous['ebitda']) / previous['ebitda']) * 100
            
            result['yoy_growth'] = growth
        
        # Calculate CAGR if we have 3+ years
        if len(periods) >= 3:
            years = len(periods) - 1
            first = periods[-1]
            latest = periods[0]
            
            cagr = {}
            
            if first['revenue'] > 0:
                cagr['revenue_cagr'] = (((latest['revenue'] / first['revenue']) ** (1/years)) - 1) * 100
            
            if first['net_income'] > 0 and latest['net_income'] > 0:
                cagr['earnings_cagr'] = (((latest['net_income'] / first['net_income']) ** (1/years)) - 1) * 100
            
            result['cagr'] = cagr
        
        # Growth rating
        yoy = result.get('yoy_growth', {})
        revenue_growth = yoy.get('revenue_growth', 0)
        earnings_growth = yoy.get('earnings_growth', 0)
        
        if revenue_growth > 20 and earnings_growth > 20:
            rating = "🔥 High Growth"
        elif revenue_growth > 10 and earnings_growth > 10:
            rating = "🟢 Moderate Growth"
        elif revenue_growth > 0 and earnings_growth > 0:
            rating = "🟡 Slow Growth"
        elif revenue_growth < 0 or earnings_growth < 0:
            rating = "🔴 Declining"
        else:
            rating = "⚪ Stagnant"
        
        result['growth_rating'] = rating
        
        return result
        
    except Exception as e:
        return {"error": str(e)}


def analyze_analyst_ratings(ticker: str) -> dict:
    """
    Analisis rekomendasi analyst dan estimasi earnings/revenue.
    
    Args:
        ticker: Stock ticker
        
    Returns:
        Dictionary dengan analyst ratings dan estimates
    """
    ticker = validate_ticker(ticker)
    ticker_jk = format_ticker(ticker)
    
    try:
        stock = yf.Ticker(ticker_jk)
        
        result = {
            "ticker": ticker.replace('.JK', ''),
            "analysis_date": datetime.now().strftime("%Y-%m-%d"),
        }
        
        # Get recommendations
        recommendations = stock.recommendations
        if recommendations is not None and not recommendations.empty:
            latest = recommendations.iloc[-1]
            
            total_analysts = (
                latest.get('strongBuy', 0) + 
                latest.get('buy', 0) + 
                latest.get('hold', 0) + 
                latest.get('sell', 0) + 
                latest.get('strongSell', 0)
            )
            
            ratings = {
                "total_analysts": int(total_analysts),
                "strong_buy": int(latest.get('strongBuy', 0)),
                "buy": int(latest.get('buy', 0)),
                "hold": int(latest.get('hold', 0)),
                "sell": int(latest.get('sell', 0)),
                "strong_sell": int(latest.get('strongSell', 0)),
            }
            
            # Calculate consensus
            bullish = ratings['strong_buy'] + ratings['buy']
            bearish = ratings['sell'] + ratings['strong_sell']
            
            if bullish > total_analysts * 0.6:
                consensus = "🟢 Strong Buy"
            elif bullish > total_analysts * 0.4:
                consensus = "🟢 Buy"
            elif bearish > total_analysts * 0.4:
                consensus = "🔴 Sell"
            else:
                consensus = "🟡 Hold"
            
            ratings['consensus'] = consensus
            result['analyst_ratings'] = ratings
        
        # Get earnings estimates
        earnings_est = stock.earnings_estimate
        if earnings_est is not None and not earnings_est.empty:
            current_q = earnings_est.iloc[0]
            next_q = earnings_est.iloc[1] if len(earnings_est) > 1 else None
            
            estimates = {
                "current_quarter": {
                    "period": earnings_est.index[0],
                    "avg_estimate": float(current_q['avg']) if 'avg' in current_q else 0,
                    "low_estimate": float(current_q['low']) if 'low' in current_q else 0,
                    "high_estimate": float(current_q['high']) if 'high' in current_q else 0,
                    "year_ago_eps": float(current_q['yearAgoEps']) if 'yearAgoEps' in current_q else 0,
                    "growth": float(current_q['growth']) * 100 if 'growth' in current_q else 0,
                },
            }
            
            if next_q is not None:
                estimates["next_quarter"] = {
                    "period": earnings_est.index[1],
                    "avg_estimate": float(next_q['avg']) if 'avg' in next_q else 0,
                    "growth": float(next_q['growth']) * 100 if 'growth' in next_q else 0,
                }
            
            result['earnings_estimates'] = estimates
        
        # Get revenue estimates
        revenue_est = stock.revenue_estimate
        if revenue_est is not None and not revenue_est.empty:
            current_q = revenue_est.iloc[0]
            
            rev_estimates = {
                "current_quarter": {
                    "period": revenue_est.index[0],
                    "avg_estimate": float(current_q['avg']) if 'avg' in current_q else 0,
                    "low_estimate": float(current_q['low']) if 'low' in current_q else 0,
                    "high_estimate": float(current_q['high']) if 'high' in current_q else 0,
                    "year_ago_revenue": float(current_q['yearAgoRevenue']) if 'yearAgoRevenue' in current_q else 0,
                    "growth": float(current_q['growth']) * 100 if 'growth' in current_q else 0,
                }
            }
            
            result['revenue_estimates'] = rev_estimates
        
        # Get earnings calendar
        calendar = stock.calendar
        if calendar:
            result['earnings_calendar'] = {
                "earnings_date": str(calendar.get('Earnings Date', ['N/A'])[0]) if 'Earnings Date' in calendar else 'N/A',
                "earnings_avg": float(calendar.get('Earnings Average', 0)) if 'Earnings Average' in calendar else 0,
                "revenue_avg": float(calendar.get('Revenue Average', 0)) if 'Revenue Average' in calendar else 0,
            }
        
        return result
        
    except Exception as e:
        return {"error": str(e)}


def analyze_dividend_history(ticker: str) -> dict:
    """
    Analisis history dividend dan yield.
    
    Args:
        ticker: Stock ticker
        
    Returns:
        Dictionary dengan dividend analysis
    """
    ticker = validate_ticker(ticker)
    ticker_jk = format_ticker(ticker)
    
    try:
        stock = yf.Ticker(ticker_jk)
        info = stock.info
        
        result = {
            "ticker": ticker.replace('.JK', ''),
        }
        
        # Get dividend history
        dividends = stock.dividends
        if len(dividends) == 0:
            result['has_dividend'] = False
            result['message'] = "Stock does not pay dividends"
            return result
        
        result['has_dividend'] = True
        
        # Recent dividends (last 5 years)
        recent_divs = dividends.tail(20)
        
        dividend_history = []
        for date, amount in recent_divs.items():
            dividend_history.append({
                "date": str(date)[:10],
                "amount": float(amount)
            })
        
        result['dividend_history'] = dividend_history[-10:]  # Last 10
        
        # Calculate stats
        if len(dividends) > 0:
            stats = {
                "total_dividends": len(dividends),
                "latest_dividend": float(dividends.iloc[-1]),
                "latest_date": str(dividends.index[-1])[:10],
            }
            
            # Annual dividend (sum of last year)
            last_year_divs = dividends[dividends.index > (dividends.index[-1] - pd.DateOffset(years=1))]
            annual_dividend = last_year_divs.sum()
            stats['annual_dividend'] = float(annual_dividend)
            
            # Dividend yield
            current_price = info.get('currentPrice', 0)
            if current_price > 0:
                stats['dividend_yield'] = (annual_dividend / current_price) * 100
            
            # Dividend growth
            if len(dividends) >= 2:
                previous_year_divs = dividends[
                    (dividends.index > (dividends.index[-1] - pd.DateOffset(years=2))) &
                    (dividends.index <= (dividends.index[-1] - pd.DateOffset(years=1)))
                ]
                if len(previous_year_divs) > 0:
                    prev_annual = previous_year_divs.sum()
                    if prev_annual > 0:
                        stats['yoy_growth'] = ((annual_dividend - prev_annual) / prev_annual) * 100
            
            # Payout consistency (dividends per year)
            years_with_divs = len(dividends.index.year.unique())
            stats['years_paying'] = years_with_divs
            stats['consistency'] = "High" if years_with_divs >= 5 else "Moderate" if years_with_divs >= 3 else "Low"
            
            result['dividend_stats'] = stats
        
        # Dividend rating
        yield_pct = result['dividend_stats'].get('dividend_yield', 0)
        consistency = result['dividend_stats'].get('consistency', 'Low')
        growth = result['dividend_stats'].get('yoy_growth', 0)
        
        if yield_pct > 5 and consistency == "High" and growth > 0:
            rating = "🔥 Excellent Dividend Stock"
        elif yield_pct > 3 and consistency in ["High", "Moderate"]:
            rating = "🟢 Good Dividend Stock"
        elif yield_pct > 2:
            rating = "🟡 Moderate Dividend"
        else:
            rating = "⚪ Low Dividend"
        
        result['dividend_rating'] = rating
        
        return result
        
    except Exception as e:
        return {"error": str(e)}


# ==================== MCP TOOL WRAPPERS ====================

def get_financial_statements_tool() -> Tool:
    """Get tool definition for financial statements analysis."""
    return Tool(
        name="get_financial_statements",
        description="Analisis lengkap laporan keuangan (Income Statement, Balance Sheet, Cash Flow). Termasuk margin analysis dan financial health score.",
        inputSchema={
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Ticker saham IDX (contoh: BBRI, BBCA, TLKM)"
                }
            },
            "required": ["ticker"]
        }
    )


async def get_financial_statements(arguments: dict) -> dict:
    """Handle financial statements analysis request."""
    ticker = arguments.get("ticker")
    result = analyze_financial_statements(ticker)
    return result


def get_earnings_growth_tool() -> Tool:
    """Get tool definition for earnings growth analysis."""
    return Tool(
        name="get_earnings_growth",
        description="Analisis pertumbuhan earnings dan revenue. Menghitung YoY growth, CAGR, dan growth rating.",
        inputSchema={
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Ticker saham IDX (contoh: BBRI, BBCA, TLKM)"
                }
            },
            "required": ["ticker"]
        }
    )


async def get_earnings_growth(arguments: dict) -> dict:
    """Handle earnings growth analysis request."""
    ticker = arguments.get("ticker")
    result = analyze_earnings_growth(ticker)
    return result


def get_analyst_ratings_tool() -> Tool:
    """Get tool definition for analyst ratings analysis."""
    return Tool(
        name="get_analyst_ratings",
        description="Rekomendasi analyst (buy/sell/hold) dan estimasi earnings/revenue. Termasuk consensus rating dan earnings calendar.",
        inputSchema={
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Ticker saham IDX (contoh: BBRI, BBCA, TLKM)"
                }
            },
            "required": ["ticker"]
        }
    )


async def get_analyst_ratings(arguments: dict) -> dict:
    """Handle analyst ratings analysis request."""
    ticker = arguments.get("ticker")
    result = analyze_analyst_ratings(ticker)
    return result


def get_dividend_history_tool() -> Tool:
    """Get tool definition for dividend history analysis."""
    return Tool(
        name="get_dividend_history",
        description="History pembayaran dividen dan analisis dividend yield. Termasuk growth rate dan consistency rating.",
        inputSchema={
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Ticker saham IDX (contoh: BBRI, BBCA, TLKM)"
                }
            },
            "required": ["ticker"]
        }
    )


async def get_dividend_history(arguments: dict) -> dict:
    """Handle dividend history analysis request."""
    ticker = arguments.get("ticker")
    result = analyze_dividend_history(ticker)
    return result
