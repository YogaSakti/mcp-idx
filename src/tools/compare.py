"""Tool for comparing stocks."""

from typing import Any, Dict
import pandas as pd
import numpy as np
from mcp.types import Tool
from src.utils.yahoo import yahoo_client, YahooFinanceError
from src.utils.validators import validate_tickers_list, validate_period


def get_compare_stocks_tool() -> Tool:
    """Get compare stocks tool definition."""
    return Tool(
        name="compare_stocks",
        description="Membandingkan performa beberapa saham.",
        inputSchema={
            "type": "object",
            "properties": {
                "tickers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List ticker saham untuk dibandingkan",
                },
                "period": {
                    "type": "string",
                    "description": "Periode perbandingan (1mo, 3mo, 6mo, 1y)",
                    "default": "1y",
                },
                "metrics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Metrik yang ingin dibandingkan (performance, valuation, dividend)",
                    "default": ["performance", "valuation"],
                },
            },
            "required": ["tickers"],
        },
    )


def calculate_performance_metrics(ticker: str, period: str) -> Dict[str, Any]:
    """
    Calculate performance metrics for a stock.

    Args:
        ticker: Stock ticker
        period: Period for calculation

    Returns:
        Dictionary with performance metrics
    """
    try:
        # Get historical data
        hist_data = yahoo_client.get_historical_data(ticker, period=period, interval="1d")
        if "error" in hist_data or not hist_data.get("data"):
            return {}

        df_data = hist_data["data"]
        df = pd.DataFrame(df_data)
        df["Date"] = pd.to_datetime(df["date"])
        df.set_index("Date", inplace=True)

        closes = df["close"].values
        if len(closes) < 2:
            return {}

        # Calculate returns
        returns = pd.Series(closes).pct_change().dropna()
        total_return = ((closes[-1] / closes[0]) - 1) * 100

        # Calculate YTD return (simplified - assumes period includes year start)
        ytd_return = total_return if period == "1y" else None

        # Calculate volatility (annualized)
        volatility = returns.std() * np.sqrt(252) * 100 if len(returns) > 1 else 0

        # Calculate Sharpe ratio (simplified, assuming risk-free rate = 0)
        sharpe_ratio = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0

        # Calculate max drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min() * 100

        return {
            "return_1y": round(total_return, 2) if period == "1y" else None,
            "return_ytd": round(ytd_return, 2) if ytd_return is not None else None,
            "volatility": round(volatility, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "max_drawdown": round(max_drawdown, 2),
        }
    except Exception:
        return {}


async def compare_stocks(args: dict[str, Any]) -> dict[str, Any]:
    """
    Compare multiple stocks.

    Args:
        args: Dictionary with 'tickers', optional 'period' and 'metrics' keys

    Returns:
        Dictionary with comparison data
    """
    try:
        tickers = validate_tickers_list(args.get("tickers", []))
        period = validate_period(args.get("period", "1y"))
        metrics = args.get("metrics", ["performance", "valuation"])

        comparison = []
        for ticker in tickers:
            try:
                # Get current price and info
                price_data = yahoo_client.get_current_price(ticker)
                info_data = yahoo_client.get_stock_info(ticker)

                stock_data = {
                    "ticker": ticker,
                    "name": price_data.get("name", ""),
                    "current_price": price_data.get("price"),
                }

                # Add performance metrics
                if "performance" in metrics:
                    perf_metrics = calculate_performance_metrics(ticker, period)
                    stock_data["performance"] = perf_metrics

                # Add valuation metrics
                if "valuation" in metrics:
                    financials = info_data.get("financials", {})
                    stock_data["valuation"] = {
                        "pe_ratio": financials.get("pe_ratio"),
                        "pb_ratio": financials.get("pb_ratio"),
                        "market_cap": info_data.get("market_cap"),
                    }

                # Add dividend metrics
                if "dividend" in metrics:
                    dividends = info_data.get("dividends", {})
                    stock_data["dividend"] = {
                        "yield": dividends.get("dividend_yield"),
                        "payout_ratio": dividends.get("payout_ratio"),
                    }

                comparison.append(stock_data)

            except Exception:
                # Skip stocks that fail
                continue

        # Calculate rankings
        ranking = {}
        if comparison:
            # Best return
            if "performance" in metrics:
                perf_stocks = [
                    (s["ticker"], s.get("performance", {}).get("return_1y") or s.get("performance", {}).get("return_ytd") or 0)
                    for s in comparison
                    if s.get("performance")
                ]
                if perf_stocks:
                    ranking["best_return"] = max(perf_stocks, key=lambda x: x[1])[0]

                # Lowest volatility
                vol_stocks = [
                    (s["ticker"], s.get("performance", {}).get("volatility", 999))
                    for s in comparison
                    if s.get("performance", {}).get("volatility") is not None
                ]
                if vol_stocks:
                    ranking["lowest_volatility"] = min(vol_stocks, key=lambda x: x[1])[0]

                # Highest Sharpe
                sharpe_stocks = [
                    (s["ticker"], s.get("performance", {}).get("sharpe_ratio", -999))
                    for s in comparison
                    if s.get("performance", {}).get("sharpe_ratio") is not None
                ]
                if sharpe_stocks:
                    ranking["highest_sharpe"] = max(sharpe_stocks, key=lambda x: x[1])[0]

            # Best value (lowest P/E)
            if "valuation" in metrics:
                pe_stocks = [
                    (s["ticker"], s.get("valuation", {}).get("pe_ratio", 999))
                    for s in comparison
                    if s.get("valuation", {}).get("pe_ratio") is not None
                ]
                if pe_stocks:
                    ranking["best_value"] = min(pe_stocks, key=lambda x: x[1])[0]

        return {
            "period": period,
            "comparison": comparison,
            "ranking": ranking,
        }

    except ValueError as e:
        return {
            "error": True,
            "code": "INVALID_PARAMETER",
            "message": str(e),
        }
    except Exception as e:
        return {
            "error": True,
            "code": "NETWORK_ERROR",
            "message": f"Gagal membandingkan saham: {str(e)}",
        }

