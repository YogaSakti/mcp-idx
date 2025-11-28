"""Tool for getting historical stock data."""

from typing import Any
from mcp.types import Tool
from src.utils.yahoo import yahoo_client, YahooFinanceError
from src.utils.validators import validate_ticker, validate_period, validate_interval
from src.config.settings import settings


def get_historical_data_tool() -> Tool:
    """Get historical data tool definition."""
    return Tool(
        name="get_historical_data",
        description="Mengambil data OHLCV (Open, High, Low, Close, Volume) untuk charting.",
        inputSchema={
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Ticker saham IDX (contoh: BBRI, BBCA, TLKM)",
                },
                "period": {
                    "type": "string",
                    "description": "Periode data (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max)",
                    "default": settings.DEFAULT_PERIOD,
                },
                "interval": {
                    "type": "string",
                    "description": "Interval data (1d, 1wk, 1mo)",
                    "default": settings.DEFAULT_INTERVAL,
                },
            },
            "required": ["ticker"],
        },
    )


async def get_historical_data(args: dict[str, Any]) -> dict[str, Any]:
    """
    Get historical stock data.

    Args:
        args: Dictionary with 'ticker', optional 'period' and 'interval' keys

    Returns:
        Dictionary with historical data
    """
    try:
        ticker = validate_ticker(args.get("ticker", ""))
        period = validate_period(args.get("period", settings.DEFAULT_PERIOD))
        interval = validate_interval(args.get("interval", settings.DEFAULT_INTERVAL))
        result = yahoo_client.get_historical_data(ticker, period=period, interval=interval)
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
            "suggestion": "Pastikan ticker valid dan periode/interval sesuai",
        }
    except Exception as e:
        return {
            "error": True,
            "code": "NETWORK_ERROR",
            "message": f"Gagal mengambil data: {str(e)}",
        }

