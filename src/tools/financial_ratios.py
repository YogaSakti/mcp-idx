"""Tool for financial ratios analysis with hybrid calculation fallback."""

from typing import Any, Dict, Optional, Tuple
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


def _sanitize_ratio(value, max_val: float = 100, min_val: float = 0) -> Optional[float]:
    """
    Sanitize financial ratios to catch Yahoo Finance data errors.
    
    Args:
        value: Raw ratio value
        max_val: Maximum reasonable value
        min_val: Minimum reasonable value (usually 0)
        
    Returns:
        Sanitized value or None if invalid/out of range
    """
    if value is None or value == 0:
        return None
    try:
        ratio = round(float(value), 2)
        if ratio < min_val or ratio > max_val:
            return None  # Return None for impossible values
        return ratio
    except (TypeError, ValueError):
        return None


def _sanitize_percentage(value, is_decimal: bool = True, max_val: float = 100, min_val: float = -100) -> Optional[float]:
    """
    Sanitize percentage values.
    
    Args:
        value: Raw value
        is_decimal: If True, multiply by 100 to convert to percentage
        max_val: Maximum reasonable percentage
        min_val: Minimum reasonable percentage
        
    Returns:
        Sanitized percentage or None if invalid
    """
    if value is None:
        return None
    try:
        pct = float(value)
        if is_decimal:
            pct = pct * 100
        pct = round(pct, 2)
        if pct < min_val or pct > max_val:
            return None
        return pct
    except (TypeError, ValueError):
        return None


def _calculate_pb_from_statements(market_cap: float, balance_sheet) -> Optional[float]:
    """
    Calculate P/B ratio from balance sheet data.
    
    P/B = Market Cap / Total Equity
    
    Args:
        market_cap: Market capitalization
        balance_sheet: Balance sheet DataFrame from yfinance
        
    Returns:
        Calculated P/B ratio or None if data unavailable
    """
    if balance_sheet is None or not market_cap:
        return None
    
    try:
        # Check if balance_sheet is empty (handle both DataFrame and None)
        if hasattr(balance_sheet, 'empty') and balance_sheet.empty:
            return None
        
        # Try different column names for total equity
        # yfinance column names can vary - use comprehensive list
        equity_columns = [
            # Standard names
            'Total Equity Gross Minority Interest',
            'Stockholders Equity',
            'Total Stockholders Equity',
            'Common Stock Equity',
            # Alternative names
            'Total Equity',
            'Equity',
            'Total Shareowners Equity',
            'Shareholders Equity',
            'Total Shareholder Equity',
            'StockholdersEquity',
            # Net worth (sometimes used)
            'Net Worth',
        ]
        
        total_equity = None
        
        # Get the index as list for case-insensitive matching
        if hasattr(balance_sheet, 'index'):
            available_indices = list(balance_sheet.index)
            
            # First try exact match
            for col in equity_columns:
                if col in available_indices:
                    val = balance_sheet.loc[col].iloc[0]
                    if val and float(val) > 0:
                        total_equity = float(val)
                        break
            
            # If not found, try case-insensitive partial match
            if total_equity is None:
                for idx in available_indices:
                    idx_lower = str(idx).lower()
                    if 'equity' in idx_lower and 'total' in idx_lower:
                        val = balance_sheet.loc[idx].iloc[0]
                        if val and float(val) > 0:
                            total_equity = float(val)
                            break
                    elif idx_lower == 'stockholders equity' or idx_lower == 'total equity':
                        val = balance_sheet.loc[idx].iloc[0]
                        if val and float(val) > 0:
                            total_equity = float(val)
                            break
        
        if total_equity and total_equity > 0:
            pb = market_cap / total_equity
            # Sanity check - P/B should be reasonable (0 to 100)
            return round(pb, 2) if 0 < pb < 100 else None
        
        return None
    except Exception:
        return None


def _calculate_ps_from_statements(market_cap: float, income_stmt) -> Optional[float]:
    """
    Calculate P/S ratio from income statement data.
    
    P/S = Market Cap / Total Revenue (TTM)
    
    Args:
        market_cap: Market capitalization
        income_stmt: Income statement DataFrame from yfinance
        
    Returns:
        Calculated P/S ratio or None if data unavailable
    """
    if income_stmt is None or not market_cap:
        return None
    
    try:
        # Check if income_stmt is empty
        if hasattr(income_stmt, 'empty') and income_stmt.empty:
            return None
        
        # Try different column names for revenue
        revenue_columns = [
            'Total Revenue',
            'Revenue',
            'Operating Revenue',
            'Net Revenue',
            'Sales',
            'Net Sales',
            'TotalRevenue',
        ]
        
        total_revenue = None
        
        if hasattr(income_stmt, 'index'):
            available_indices = list(income_stmt.index)
            
            # First try exact match
            for col in revenue_columns:
                if col in available_indices:
                    val = income_stmt.loc[col].iloc[0]
                    if val and float(val) > 0:
                        total_revenue = float(val)
                        break
            
            # If not found, try case-insensitive partial match
            if total_revenue is None:
                for idx in available_indices:
                    idx_lower = str(idx).lower()
                    if 'revenue' in idx_lower and ('total' in idx_lower or idx_lower == 'revenue'):
                        val = income_stmt.loc[idx].iloc[0]
                        if val and float(val) > 0:
                            total_revenue = float(val)
                            break
        
        if total_revenue and total_revenue > 0:
            ps = market_cap / total_revenue
            return round(ps, 2) if 0 < ps < 100 else None
        
        return None
    except Exception:
        return None


def _calculate_dividend_yield_from_data(current_price: float, ticker_obj) -> Optional[float]:
    """
    Calculate dividend yield from dividend history.
    
    Dividend Yield = (Annual Dividend / Current Price) × 100
    
    Args:
        current_price: Current stock price
        ticker_obj: yfinance Ticker object
        
    Returns:
        Calculated dividend yield percentage or None
    """
    if not current_price or current_price <= 0:
        return None
    
    try:
        import pandas as pd
        from datetime import datetime, timedelta
        
        dividends = ticker_obj.dividends
        if dividends is None or len(dividends) == 0:
            return None
        
        # Get dividends from last 12 months
        one_year_ago = datetime.now() - timedelta(days=365)
        recent_divs = dividends[dividends.index > one_year_ago]
        
        if len(recent_divs) == 0:
            return None
        
        annual_dividend = recent_divs.sum()
        
        if annual_dividend <= 0:
            return None
        
        dividend_yield = (annual_dividend / current_price) * 100
        
        # Sanity check - yield > 50% is extremely rare
        return round(dividend_yield, 2) if 0 < dividend_yield < 50 else None
    except Exception:
        return None


def _get_ratio_with_fallback(
    yahoo_value: Optional[float],
    calculated_value: Optional[float],
    max_val: float = 100,
    min_val: float = 0
) -> Tuple[Optional[float], str]:
    """
    Get ratio value with fallback logic.
    
    Priority:
    1. Yahoo value if valid
    2. Calculated value as fallback
    3. None if both invalid
    
    Args:
        yahoo_value: Value from Yahoo Finance
        calculated_value: Manually calculated value
        max_val: Maximum reasonable value
        min_val: Minimum reasonable value
        
    Returns:
        Tuple of (value, source) where source is "yahoo", "calculated", or "none"
    """
    # Try Yahoo value first
    yahoo_sanitized = _sanitize_ratio(yahoo_value, max_val=max_val, min_val=min_val)
    if yahoo_sanitized is not None:
        return yahoo_sanitized, "yahoo"
    
    # Fallback to calculated value
    if calculated_value is not None:
        calculated_sanitized = _sanitize_ratio(calculated_value, max_val=max_val, min_val=min_val)
        if calculated_sanitized is not None:
            return calculated_sanitized, "calculated"
    
    return None, "none"


def calculate_ratios(
    info: Dict[str, Any],
    current_price: float,
    ticker_obj=None,
    market_cap: Optional[float] = None
) -> Dict[str, Any]:
    """
    Calculate financial ratios from Yahoo Finance info with hybrid fallback.
    
    If Yahoo provides invalid data (e.g., P/B = 11878), we calculate
    the ratio manually from financial statements.
    
    Args:
        info: Yahoo Finance info dictionary
        current_price: Current stock price
        ticker_obj: yfinance Ticker object for statement access
        market_cap: Market capitalization
        
    Returns:
        Dictionary with calculated ratios (includes source field)
    """
    ratios = {}
    
    # Get financial statements for fallback calculations
    balance_sheet = None
    income_stmt = None
    
    if ticker_obj:
        try:
            balance_sheet = ticker_obj.balance_sheet
            income_stmt = ticker_obj.income_stmt
        except Exception:
            pass
    
    # Use market_cap from info if not provided
    if not market_cap:
        market_cap = info.get("marketCap")
    
    # ==================== VALUATION RATIOS ====================
    
    # P/E Ratio - Yahoo only (hard to calculate accurately)
    pe_ratio = _sanitize_ratio(info.get("trailingPE") or info.get("forwardPE"), max_val=1000, min_val=0)
    ratios["pe_ratio"] = {
        "value": pe_ratio,
        "source": "yahoo" if pe_ratio else "none",
        "interpretation": (
            "undervalued" if pe_ratio and pe_ratio < 15
            else "fair" if pe_ratio and 15 <= pe_ratio <= 25
            else "overvalued" if pe_ratio and pe_ratio > 25
            else None
        ),
        "description": "Price-to-Earnings ratio"
    }
    
    # P/B Ratio - WITH HYBRID FALLBACK
    yahoo_pb = info.get("priceToBook")
    calculated_pb = _calculate_pb_from_statements(market_cap, balance_sheet) if market_cap else None
    pb_ratio, pb_source = _get_ratio_with_fallback(yahoo_pb, calculated_pb, max_val=100, min_val=0)
    
    # Store raw Yahoo value for transparency if calculated fallback was used
    pb_entry = {
        "value": pb_ratio,
        "source": pb_source,
        "interpretation": (
            "undervalued" if pb_ratio and pb_ratio < 1
            else "fair" if pb_ratio and 1 <= pb_ratio <= 3
            else "overvalued" if pb_ratio and pb_ratio > 3
            else None
        ),
        "description": "Price-to-Book ratio"
    }
    if pb_source == "calculated" and yahoo_pb:
        pb_entry["yahoo_raw"] = round(float(yahoo_pb), 2) if yahoo_pb else None
    ratios["pb_ratio"] = pb_entry
    
    # P/S Ratio - WITH HYBRID FALLBACK
    yahoo_ps = info.get("priceToSalesTrailing12Months")
    calculated_ps = _calculate_ps_from_statements(market_cap, income_stmt) if market_cap else None
    ps_ratio, ps_source = _get_ratio_with_fallback(yahoo_ps, calculated_ps, max_val=100, min_val=0)
    
    ps_entry = {
        "value": ps_ratio,
        "source": ps_source,
        "interpretation": (
            "undervalued" if ps_ratio and ps_ratio < 1
            else "fair" if ps_ratio and 1 <= ps_ratio <= 3
            else "overvalued" if ps_ratio and ps_ratio > 3
            else None
        ),
        "description": "Price-to-Sales ratio"
    }
    if ps_source == "calculated" and yahoo_ps:
        ps_entry["yahoo_raw"] = round(float(yahoo_ps), 2) if yahoo_ps else None
    ratios["ps_ratio"] = ps_entry
    
    # ==================== PROFITABILITY RATIOS ====================
    
    roe_percent = _sanitize_percentage(info.get("returnOnEquity"), is_decimal=True, max_val=200, min_val=-100)
    if roe_percent is not None:
        ratios["roe"] = {
            "value": roe_percent,
            "source": "yahoo",
            "interpretation": (
                "excellent" if roe_percent >= 15
                else "good" if roe_percent >= 10
                else "fair" if roe_percent >= 5
                else "poor"
            ),
            "description": "Return on Equity (%)"
        }
    
    roa_percent = _sanitize_percentage(info.get("returnOnAssets"), is_decimal=True, max_val=100, min_val=-50)
    if roa_percent is not None:
        ratios["roa"] = {
            "value": roa_percent,
            "source": "yahoo",
            "interpretation": (
                "excellent" if roa_percent >= 10
                else "good" if roa_percent >= 5
                else "fair" if roa_percent >= 2
                else "poor"
            ),
            "description": "Return on Assets (%)"
        }
    
    profit_margin_percent = _sanitize_percentage(info.get("profitMargins"), is_decimal=True, max_val=100, min_val=-100)
    if profit_margin_percent is not None:
        ratios["profit_margin"] = {
            "value": profit_margin_percent,
            "source": "yahoo",
            "interpretation": (
                "excellent" if profit_margin_percent >= 20
                else "good" if profit_margin_percent >= 10
                else "fair" if profit_margin_percent >= 5
                else "poor"
            ),
            "description": "Profit Margin (%)"
        }
    
    # ==================== LEVERAGE RATIOS ====================
    
    debt_to_equity = info.get("debtToEquity")
    ratios["debt_to_equity"] = {
        "value": round(debt_to_equity, 2) if debt_to_equity else None,
        "source": "yahoo" if debt_to_equity else "none",
        "interpretation": (
            "low" if debt_to_equity and debt_to_equity < 0.5
            else "moderate" if debt_to_equity and 0.5 <= debt_to_equity <= 1.0
            else "high" if debt_to_equity and debt_to_equity > 1.0
            else None
        ),
        "description": "Debt-to-Equity ratio"
    }
    
    # ==================== LIQUIDITY RATIOS ====================
    
    current_ratio = info.get("currentRatio")
    ratios["current_ratio"] = {
        "value": round(current_ratio, 2) if current_ratio else None,
        "source": "yahoo" if current_ratio else "none",
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
        "source": "yahoo" if quick_ratio else "none",
        "interpretation": (
            "excellent" if quick_ratio and quick_ratio >= 1.0
            else "good" if quick_ratio and 0.5 <= quick_ratio < 1.0
            else "poor" if quick_ratio and quick_ratio < 0.5
            else None
        ),
        "description": "Quick Ratio"
    }
    
    # ==================== DIVIDEND RATIOS - WITH HYBRID FALLBACK ====================
    
    yahoo_div_yield = info.get("dividendYield")
    yahoo_div_yield_pct = _sanitize_percentage(yahoo_div_yield, is_decimal=True, max_val=50, min_val=0)
    
    # Fallback calculation from dividend history
    calculated_div_yield = None
    if yahoo_div_yield_pct is None and ticker_obj:
        calculated_div_yield = _calculate_dividend_yield_from_data(current_price, ticker_obj)
    
    # Determine which value to use
    if yahoo_div_yield_pct is not None:
        div_yield_value = yahoo_div_yield_pct
        div_source = "yahoo"
    elif calculated_div_yield is not None:
        div_yield_value = calculated_div_yield
        div_source = "calculated"
    else:
        div_yield_value = None
        div_source = "none"
    
    if div_yield_value is not None:
        div_entry = {
            "value": div_yield_value,
            "source": div_source,
            "interpretation": (
                "high" if div_yield_value >= 5
                else "moderate" if div_yield_value >= 2
                else "low" if div_yield_value > 0
                else "none"
            ),
            "description": "Dividend Yield (%)"
        }
        if div_source == "calculated" and yahoo_div_yield:
            # Show raw Yahoo value for transparency
            div_entry["yahoo_raw"] = round(float(yahoo_div_yield) * 100, 2)
        ratios["dividend_yield"] = div_entry
    
    # Payout ratio - Yahoo only
    payout_ratio_percent = _sanitize_percentage(info.get("payoutRatio"), is_decimal=True, max_val=200, min_val=0)
    if payout_ratio_percent is not None:
        ratios["payout_ratio"] = {
            "value": payout_ratio_percent,
            "source": "yahoo",
            "interpretation": (
                "high" if payout_ratio_percent >= 80
                else "moderate" if payout_ratio_percent >= 50
                else "low" if payout_ratio_percent > 0
                else "none"
            ),
            "description": "Payout Ratio (%)"
        }
    
    # ==================== GROWTH METRICS ====================
    
    earnings_growth = info.get("earningsQuarterlyGrowth")
    if earnings_growth:
        earnings_growth_percent = earnings_growth * 100
        ratios["earnings_growth"] = {
            "value": round(earnings_growth_percent, 2),
            "source": "yahoo",
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
            "source": "yahoo",
            "interpretation": (
                "strong" if revenue_growth_percent >= 15
                else "moderate" if revenue_growth_percent >= 5
                else "slow" if revenue_growth_percent >= 0
                else "declining"
            ),
            "description": "Revenue Growth (%)"
        }
    
    # ==================== ADDITIONAL METRICS ====================
    
    eps = info.get("trailingEps") or info.get("forwardEps")
    ratios["eps"] = {
        "value": round(eps, 2) if eps else None,
        "source": "yahoo" if eps else "none",
        "description": "Earnings Per Share"
    }
    
    book_value = info.get("bookValue")
    ratios["book_value"] = {
        "value": round(book_value, 2) if book_value else None,
        "source": "yahoo" if book_value else "none",
        "description": "Book Value per Share"
    }
    
    return ratios


async def get_financial_ratios(args: dict[str, Any]) -> dict[str, Any]:
    """
    Get comprehensive financial ratios analysis with hybrid fallback.
    
    If Yahoo Finance returns invalid/impossible values (e.g., P/B = 11878),
    we calculate the ratios manually from financial statements.
    
    Args:
        args: Dictionary with 'ticker' key
        
    Returns:
        Dictionary with financial ratios analysis (includes data source info)
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
        
        # Get market cap for fallback calculations
        market_cap = info.get("marketCap")
        
        # Calculate ratios with hybrid fallback (pass ticker_obj for statement access)
        ratios = calculate_ratios(info, current_price, ticker_obj=ticker_obj, market_cap=market_cap)
        
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
        
        # Count how many ratios used calculated fallback
        calculated_count = sum(1 for r in ratios.values() if isinstance(r, dict) and r.get("source") == "calculated")
        
        result = {
            "ticker": ticker,
            "name": name,
            "sector": sector,
            "industry": industry,
            "current_price": round(current_price, 2),
            "market_cap": market_cap,
            "financial_score": round(financial_score, 1) if financial_score else None,
            "data_quality": {
                "calculated_fallback_count": calculated_count,
                "note": "Some ratios calculated from financial statements due to invalid Yahoo data" if calculated_count > 0 else "All ratios from Yahoo Finance"
            },
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

