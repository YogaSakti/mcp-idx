"""Tool for getting watchlist prices."""

from typing import Any
from mcp.types import Tool
from src.utils.yahoo import yahoo_client, YahooFinanceError
from src.utils.validators import validate_tickers_list


def get_watchlist_prices_tool() -> Tool:
    """Get watchlist prices tool definition."""
    return Tool(
        name="get_watchlist_prices",
        description="Mengambil harga untuk multiple tickers sekaligus (batch).",
        inputSchema={
            "type": "object",
            "properties": {
                "tickers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List ticker saham (contoh: [\"BBCA\", \"BBRI\", \"TLKM\"])",
                },
            },
            "required": ["tickers"],
        },
    )


async def get_watchlist_prices(args: dict[str, Any]) -> dict[str, Any]:
    """
    Get prices for multiple tickers.

    Args:
        args: Dictionary with 'tickers' key (list of ticker symbols)

    Returns:
        Dictionary with prices for all tickers
    """
    try:
        tickers = validate_tickers_list(args.get("tickers", []))
        result = yahoo_client.get_multiple_prices(tickers)
        return result
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
            "message": f"Gagal mengambil harga: {str(e)}",
        }

