"""Tool for getting stock prices."""

from typing import Any
from mcp.types import Tool
from src.utils.yahoo import yahoo_client, YahooFinanceError
from src.utils.validators import validate_ticker
from src.utils.exceptions import InvalidParameterError, DataUnavailableError, NetworkError


def get_stock_price_tool() -> Tool:
    """Get stock price tool definition."""
    return Tool(
        name="get_stock_price",
        description="Mengambil harga saham terkini beserta perubahan harian untuk ticker IDX tertentu.",
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


async def get_stock_price(args: dict[str, Any]) -> dict[str, Any]:
    """
    Get current stock price.

    Args:
        args: Dictionary with 'ticker' key

    Returns:
        Dictionary with price data
        
    Raises:
        MCPToolError: If there's an error getting the price
    """
    try:
        ticker = validate_ticker(args.get("ticker", ""))
        result = yahoo_client.get_current_price(ticker)
        return result
    except ValueError as e:
        raise InvalidParameterError(str(e))
    except YahooFinanceError as e:
        raise DataUnavailableError(str(e))
    except Exception as e:
        raise NetworkError(f"Gagal mengambil data: {str(e)}")

