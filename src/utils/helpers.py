"""Helper functions for ticker formatting and utilities."""

from typing import Optional
from src.config.settings import settings


def format_ticker(ticker: str) -> str:
    """
    Format ticker to Yahoo Finance format (add .JK suffix if not present).

    Args:
        ticker: Stock ticker symbol (e.g., "BBCA" or "BBCA.JK")

    Returns:
        Formatted ticker with .JK suffix (e.g., "BBCA.JK")
    """
    ticker = ticker.upper().strip()
    if not ticker.endswith(settings.IDX_SUFFIX):
        ticker = f"{ticker}{settings.IDX_SUFFIX}"
    return ticker


def normalize_ticker(ticker: str) -> str:
    """
    Normalize ticker by removing suffix (for display purposes).

    Args:
        ticker: Stock ticker symbol (e.g., "BBCA.JK")

    Returns:
        Ticker without suffix (e.g., "BBCA")
    """
    ticker = ticker.upper().strip()
    if ticker.endswith(settings.IDX_SUFFIX):
        ticker = ticker[: -len(settings.IDX_SUFFIX)]
    return ticker


def is_market_hours() -> bool:
    """
    Check if market is currently open (simplified check).

    Returns:
        True if market is open, False otherwise
    """
    from datetime import datetime
    import pytz

    jakarta_tz = pytz.timezone(settings.MARKET_TIMEZONE)
    now = datetime.now(jakarta_tz)
    current_time = now.time()

    # Parse market hours
    open_hour, open_minute = map(int, settings.MARKET_OPEN.split(":"))
    close_hour, close_minute = map(int, settings.MARKET_CLOSE.split(":"))

    market_open = datetime.now(jakarta_tz).replace(
        hour=open_hour, minute=open_minute, second=0, microsecond=0
    ).time()
    market_close = datetime.now(jakarta_tz).replace(
        hour=close_hour, minute=close_minute, second=0, microsecond=0
    ).time()

    # Check if it's a weekday (Monday=0, Sunday=6)
    is_weekday = now.weekday() < 5

    return is_weekday and market_open <= current_time <= market_close


def format_number(value: Optional[float], decimals: int = 2) -> Optional[float]:
    """
    Format number to specified decimal places.

    Args:
        value: Number to format
        decimals: Number of decimal places

    Returns:
        Formatted number or None if value is None
    """
    if value is None:
        return None
    return round(value, decimals)

