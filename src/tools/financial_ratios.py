"""Tool for financial ratios analysis."""

from typing import Any, Dict, Optional
from mcp.types import Tool
from src.utils.yahoo import yahoo_client, YahooFinanceError
from src.utils.validators import validate_ticker
from src.utils.exceptions import InvalidParameterError, DataUnavailableError, NetworkError
from src.utils.cache import cache_manager


def get_financial_ratios_tool() -> Tool:
    """Get financial ratios tool definition."""
    return Tool(
        name="get_financial_ratios",
        description="Menganalisis rasio keuangan fundamental untuk ticker IDX tertentu. Menghitung P/E, P/B, ROE, ROA, Debt-to-Equity, Current Ratio, dan growth metrics.",
        inputSchema={
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Ticker saham IDX (contoh: BBCA, BBRI, TLKM)",
                },
            },
            "required": ["ticker"],
        },
    )


def calculate_ratios(info: Dict[str, Any], current_price: float) -> Dict[str, Any]:
    """
    Calculate financial ratios from Yahoo Finance info.
    
    Args:
        info: Yahoo Finance info dictionary
        current_price: Current stock price
        
    Returns:
        Dictionary with calculated ratios
    """
    ratios = {}
    
    # Valuation Ratios
    pe_ratio = info.get("trailingPE") or info.get("forwardPE")
    ratios["pe_ratio"] = {
        "value": round(pe_ratio, 2) if pe_ratio else None,
        "interpretation": (
            "undervalued" if pe_ratio and pe_ratio < 15
            else "fair" if pe_ratio and 15 <= pe_ratio <= 25
            else "overvalued" if pe_ratio and pe_ratio > 25
            else None
        ),
        "description": "Price-to-Earnings ratio"
    }
    
    pb_ratio = info.get("priceToBook")
    ratios["pb_ratio"] = {
        "value": round(pb_ratio, 2) if pb_ratio else None,
        "interpretation": (
            "undervalued" if pb_ratio and pb_ratio < 1
            else "fair" if pb_ratio and 1 <= pb_ratio <= 3
            else "overvalued" if pb_ratio and pb_ratio > 3
            else None
        ),
        "description": "Price-to-Book ratio"
    }
    
    ps_ratio = info.get("priceToSalesTrailing12Months")
    ratios["ps_ratio"] = {
        "value": round(ps_ratio, 2) if ps_ratio else None,
        "interpretation": (
            "undervalued" if ps_ratio and ps_ratio < 1
            else "fair" if ps_ratio and 1 <= ps_ratio <= 3
            else "overvalued" if ps_ratio and ps_ratio > 3
            else None
        ),
        "description": "Price-to-Sales ratio"
    }
    
    # Profitability Ratios
    roe = info.get("returnOnEquity")
    if roe:
        roe_percent = roe * 100
        ratios["roe"] = {
            "value": round(roe_percent, 2),
            "interpretation": (
                "excellent" if roe_percent >= 15
                else "good" if roe_percent >= 10
                else "fair" if roe_percent >= 5
                else "poor"
            ),
            "description": "Return on Equity (%)"
        }
    
    roa = info.get("returnOnAssets")
    if roa:
        roa_percent = roa * 100
        ratios["roa"] = {
            "value": round(roa_percent, 2),
            "interpretation": (
                "excellent" if roa_percent >= 10
                else "good" if roa_percent >= 5
                else "fair" if roa_percent >= 2
                else "poor"
            ),
            "description": "Return on Assets (%)"
        }
    
    profit_margin = info.get("profitMargins")
    if profit_margin:
        profit_margin_percent = profit_margin * 100
        ratios["profit_margin"] = {
            "value": round(profit_margin_percent, 2),
            "interpretation": (
                "excellent" if profit_margin_percent >= 20
                else "good" if profit_margin_percent >= 10
                else "fair" if profit_margin_percent >= 5
                else "poor"
            ),
            "description": "Profit Margin (%)"
        }
    
    # Leverage Ratios
    debt_to_equity = info.get("debtToEquity")
    ratios["debt_to_equity"] = {
        "value": round(debt_to_equity, 2) if debt_to_equity else None,
        "interpretation": (
            "low" if debt_to_equity and debt_to_equity < 0.5
            else "moderate" if debt_to_equity and 0.5 <= debt_to_equity <= 1.0
            else "high" if debt_to_equity and debt_to_equity > 1.0
            else None
        ),
        "description": "Debt-to-Equity ratio"
    }
    
    # Liquidity Ratios
    current_ratio = info.get("currentRatio")
    ratios["current_ratio"] = {
        "value": round(current_ratio, 2) if current_ratio else None,
        "interpretation": (
            "excellent" if current_ratio and current_ratio >= 2.0
            else "good" if current_ratio and 1.5 <= current_ratio < 2.0
            else "fair" if current_ratio and 1.0 <= current_ratio < 1.5
            else "poor" if current_ratio and current_ratio < 1.0
            else None
        ),
        "description": "Current Ratio"
    }
    
    quick_ratio = info.get("quickRatio")
    ratios["quick_ratio"] = {
        "value": round(quick_ratio, 2) if quick_ratio else None,
        "interpretation": (
            "excellent" if quick_ratio and quick_ratio >= 1.0
            else "good" if quick_ratio and 0.5 <= quick_ratio < 1.0
            else "poor" if quick_ratio and quick_ratio < 0.5
            else None
        ),
        "description": "Quick Ratio"
    }
    
    # Dividend Ratios
    dividend_yield = info.get("dividendYield")
    if dividend_yield:
        dividend_yield_percent = dividend_yield * 100
        ratios["dividend_yield"] = {
            "value": round(dividend_yield_percent, 2),
            "interpretation": (
                "high" if dividend_yield_percent >= 5
                else "moderate" if dividend_yield_percent >= 2
                else "low" if dividend_yield_percent > 0
                else "none"
            ),
            "description": "Dividend Yield (%)"
        }
    
    payout_ratio = info.get("payoutRatio")
    if payout_ratio:
        payout_ratio_percent = payout_ratio * 100
        ratios["payout_ratio"] = {
            "value": round(payout_ratio_percent, 2),
            "interpretation": (
                "high" if payout_ratio_percent >= 80
                else "moderate" if payout_ratio_percent >= 50
                else "low" if payout_ratio_percent > 0
                else "none"
            ),
            "description": "Payout Ratio (%)"
        }
    
    # Growth Metrics
    earnings_growth = info.get("earningsQuarterlyGrowth")
    if earnings_growth:
        earnings_growth_percent = earnings_growth * 100
        ratios["earnings_growth"] = {
            "value": round(earnings_growth_percent, 2),
            "interpretation": (
                "strong" if earnings_growth_percent >= 20
                else "moderate" if earnings_growth_percent >= 10
                else "slow" if earnings_growth_percent >= 0
                else "declining"
            ),
            "description": "Earnings Growth (Quarterly, %)"
        }
    
    revenue_growth = info.get("revenueGrowth")
    if revenue_growth:
        revenue_growth_percent = revenue_growth * 100
        ratios["revenue_growth"] = {
            "value": round(revenue_growth_percent, 2),
            "interpretation": (
                "strong" if revenue_growth_percent >= 15
                else "moderate" if revenue_growth_percent >= 5
                else "slow" if revenue_growth_percent >= 0
                else "declining"
            ),
            "description": "Revenue Growth (%)"
        }
    
    # Additional Metrics
    eps = info.get("trailingEps") or info.get("forwardEps")
    ratios["eps"] = {
        "value": round(eps, 2) if eps else None,
        "description": "Earnings Per Share"
    }
    
    book_value = info.get("bookValue")
    ratios["book_value"] = {
        "value": round(book_value, 2) if book_value else None,
        "description": "Book Value per Share"
    }
    
    return ratios


async def get_financial_ratios(args: dict[str, Any]) -> dict[str, Any]:
    """
    Get comprehensive financial ratios analysis.
    
    Args:
        args: Dictionary with 'ticker' key
        
    Returns:
        Dictionary with financial ratios analysis
    """
    try:
        ticker = validate_ticker(args.get("ticker", ""))
        
        # Check cache
        cache_key = cache_manager.generate_key("financial_ratios", ticker)
        cached = cache_manager.get("financial_ratios", cache_key)
        if cached:
            return cached
        
        # Get ticker object and info
        ticker_obj = yahoo_client.get_ticker(ticker)
        info = ticker_obj.info
        
        if not info:
            raise DataUnavailableError(f"Tidak ada data financial untuk ticker {ticker}")
        
        # Get current price
        price_data = yahoo_client.get_current_price(ticker)
        current_price = price_data.get("price", 0)
        
        if not current_price:
            raise DataUnavailableError(f"Tidak dapat mengambil harga untuk ticker {ticker}")
        
        # Calculate ratios
        ratios = calculate_ratios(info, current_price)
        
        # Get basic info
        name = info.get("longName") or info.get("shortName", "")
        sector = info.get("sector", "")
        industry = info.get("industry", "")
        market_cap = info.get("marketCap")
        
        # Calculate summary score (simple scoring)
        score_components = []
        if ratios.get("pe_ratio", {}).get("value"):
            pe_val = ratios["pe_ratio"]["value"]
            if pe_val and 10 <= pe_val <= 20:
                score_components.append(1)
        if ratios.get("roe", {}).get("value"):
            roe_val = ratios["roe"]["value"]
            if roe_val and roe_val >= 15:
                score_components.append(1)
        if ratios.get("profit_margin", {}).get("value"):
            pm_val = ratios["profit_margin"]["value"]
            if pm_val and pm_val >= 10:
                score_components.append(1)
        if ratios.get("debt_to_equity", {}).get("value"):
            dte_val = ratios["debt_to_equity"]["value"]
            if dte_val and dte_val <= 1.0:
                score_components.append(1)
        
        financial_score = len(score_components) / 4 * 100 if score_components else None
        
        result = {
            "ticker": ticker,
            "name": name,
            "sector": sector,
            "industry": industry,
            "current_price": round(current_price, 2),
            "market_cap": market_cap,
            "financial_score": round(financial_score, 1) if financial_score else None,
            "ratios": ratios,
            "summary": {
                "valuation": {
                    "pe_ratio": ratios.get("pe_ratio", {}).get("value"),
                    "pb_ratio": ratios.get("pb_ratio", {}).get("value"),
                    "ps_ratio": ratios.get("ps_ratio", {}).get("value"),
                },
                "profitability": {
                    "roe": ratios.get("roe", {}).get("value"),
                    "roa": ratios.get("roa", {}).get("value"),
                    "profit_margin": ratios.get("profit_margin", {}).get("value"),
                },
                "leverage": {
                    "debt_to_equity": ratios.get("debt_to_equity", {}).get("value"),
                },
                "liquidity": {
                    "current_ratio": ratios.get("current_ratio", {}).get("value"),
                    "quick_ratio": ratios.get("quick_ratio", {}).get("value"),
                },
                "dividend": {
                    "dividend_yield": ratios.get("dividend_yield", {}).get("value"),
                    "payout_ratio": ratios.get("payout_ratio", {}).get("value"),
                },
                "growth": {
                    "earnings_growth": ratios.get("earnings_growth", {}).get("value"),
                    "revenue_growth": ratios.get("revenue_growth", {}).get("value"),
                },
            }
        }
        
        # Cache result
        cache_manager.set("financial_ratios", cache_key, result)
        
        return result
        
    except ValueError as e:
        raise InvalidParameterError(str(e))
    except YahooFinanceError as e:
        raise DataUnavailableError(str(e))
    except Exception as e:
        raise NetworkError(f"Gagal mengambil financial ratios: {str(e)}")

