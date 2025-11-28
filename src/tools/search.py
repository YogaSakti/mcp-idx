"""Tool for searching stocks."""

from typing import Any, List, Dict
import json
import os
from mcp.types import Tool
from src.utils.yahoo import yahoo_client, YahooFinanceError
from src.utils.validators import SearchQueryValidator


def get_search_stocks_tool() -> Tool:
    """Get search stocks tool definition."""
    return Tool(
        name="search_stocks",
        description="Mencari saham berdasarkan nama atau ticker.",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Kata kunci pencarian (nama perusahaan atau ticker)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Jumlah maksimal hasil (default: 10)",
                    "default": 10,
                },
                "sector": {
                    "type": "string",
                    "description": "Filter berdasarkan sektor (opsional)",
                },
            },
            "required": ["query"],
        },
    )


def load_ticker_list() -> List[Dict[str, Any]]:
    """
    Load ticker list from JSON file.

    Returns:
        List of ticker dictionaries
    """
    try:
        config_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        tickers_file = os.path.join(config_dir, "src", "config", "tickers.json")
        with open(tickers_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("tickers", [])
    except Exception:
        return []


async def search_stocks(args: dict[str, Any]) -> dict[str, Any]:
    """
    Search for stocks.

    Args:
        args: Dictionary with 'query', optional 'limit' and 'sector' keys

    Returns:
        Dictionary with search results
    """
    try:
        validator = SearchQueryValidator(**args)
        query = validator.query.lower()
        limit = validator.limit
        sector = validator.sector

        # Load ticker list
        tickers = load_ticker_list()

        # Filter tickers
        results = []
        for ticker_info in tickers:
            ticker_name = ticker_info.get("name", "").lower()
            ticker_symbol = ticker_info.get("ticker", "").lower()
            ticker_sector = ticker_info.get("sector", "")

            # Check if query matches
            matches_query = query in ticker_name or query in ticker_symbol
            matches_sector = sector is None or sector.lower() == ticker_sector.lower()

            if matches_query and matches_sector:
                try:
                    # Get current price
                    price_data = yahoo_client.get_current_price(ticker_info["ticker"])
                    results.append({
                        "ticker": ticker_info["ticker"],
                        "name": ticker_info["name"],
                        "sector": ticker_info.get("sector", ""),
                        "market_cap": price_data.get("market_cap"),
                        "price": price_data.get("price"),
                        "change_percent": price_data.get("change_percent", 0),
                    })
                except Exception:
                    # If price fetch fails, still include basic info
                    results.append({
                        "ticker": ticker_info["ticker"],
                        "name": ticker_info["name"],
                        "sector": ticker_info.get("sector", ""),
                        "market_cap": None,
                        "price": None,
                        "change_percent": None,
                    })

        # Sort by market cap (descending) if available
        results.sort(
            key=lambda x: x["market_cap"] if x["market_cap"] else 0,
            reverse=True
        )

        # Limit results
        showing = min(len(results), limit)
        results = results[:showing]

        return {
            "query": validator.query,
            "total_results": len(results),
            "showing": showing,
            "results": results,
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
            "message": f"Gagal mencari saham: {str(e)}",
        }

