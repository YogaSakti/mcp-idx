"""Application configuration settings."""

import os
from typing import List


class Settings:
    """Application settings and configuration."""

    # Ticker format
    IDX_SUFFIX = ".JK"

    # Default values
    DEFAULT_PERIOD = "1mo"
    DEFAULT_INTERVAL = "1d"
    DEFAULT_INDICATORS: List[str] = ["rsi", "macd", "sma_20"]

    # Limits
    MAX_TICKERS_PER_REQUEST = 20
    MAX_HISTORY_PERIOD = "5y"

    # Market hours (WIB)
    MARKET_OPEN = "09:00"
    MARKET_CLOSE = "16:00"
    MARKET_TIMEZONE = "Asia/Jakarta"

    # Yahoo Finance
    YAHOO_TIMEOUT = int(os.getenv("YAHOO_TIMEOUT", "30"))

    # Caching
    CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    CACHE_MAX_SIZE = int(os.getenv("CACHE_MAX_SIZE", "1000"))

    # Rate Limiting
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_PERIOD = int(os.getenv("RATE_LIMIT_PERIOD", "60"))

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "idx-stock-mcp.log")


# Global settings instance
settings = Settings()

