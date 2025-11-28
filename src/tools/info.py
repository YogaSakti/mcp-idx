"""Tool for getting stock information."""

from typing import Any
from mcp.types import Tool
from src.utils.yahoo import yahoo_client, YahooFinanceError
from src.utils.validators import validate_ticker


def get_stock_info_tool() -> Tool:
    """Get stock info tool definition."""
    return Tool(
        name="get_stock_info",
        description="Mengambil informasi fundamental perusahaan untuk ticker IDX tertentu.",
        inputSchema={
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Ticker saham IDX (contoh: ASII, BBCA, TLKM)",
                },
            },
            "required": ["ticker"],
        },
    )


async def get_stock_info(args: dict[str, Any]) -> dict[str, Any]:
    """
    Get stock information.

    Args:
        args: Dictionary with 'ticker' key

    Returns:
        Dictionary with stock info
    """
    try:
        ticker = validate_ticker(args.get("ticker", ""))
        result = yahoo_client.get_stock_info(ticker)
        return result
    except ValueError as e:
        return {
            "error": True,
            "code": "INVALID_PARAMETER",
            "message": str(e),
        }
    except YahooFinanceError as e:
        return {
            "error": True,
            "code": "DATA_UNAVAILABLE",
            "message": str(e),
            "suggestion": "Pastikan ticker valid dan coba lagi",
        }
    except Exception as e:
        return {
            "error": True,
            "code": "NETWORK_ERROR",
            "message": f"Gagal mengambil data: {str(e)}",
        }

