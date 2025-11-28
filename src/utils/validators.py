"""Input validation utilities."""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from src.config.settings import settings


class TickerValidator(BaseModel):
    """Validator for ticker input."""

    ticker: str = Field(..., min_length=1, max_length=20)

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        """Validate and normalize ticker."""
        ticker = v.upper().strip()
        if not ticker:
            raise ValueError("Ticker cannot be empty")
        return ticker


class PeriodValidator(BaseModel):
    """Validator for period input."""

    period: str = Field(default=settings.DEFAULT_PERIOD)

    @field_validator("period")
    @classmethod
    def validate_period(cls, v: str) -> str:
        """Validate period format."""
        valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"]
        if v not in valid_periods:
            raise ValueError(
                f"Period must be one of: {', '.join(valid_periods)}"
            )
        return v


class IntervalValidator(BaseModel):
    """Validator for interval input."""

    interval: str = Field(default=settings.DEFAULT_INTERVAL)

    @field_validator("interval")
    @classmethod
    def validate_interval(cls, v: str) -> str:
        """Validate interval format."""
        valid_intervals = ["1d", "1wk", "1mo"]
        if v not in valid_intervals:
            raise ValueError(
                f"Interval must be one of: {', '.join(valid_intervals)}"
            )
        return v


class IndicatorsValidator(BaseModel):
    """Validator for indicators input."""

    indicators: List[str] = Field(default=settings.DEFAULT_INDICATORS)

    @field_validator("indicators")
    @classmethod
    def validate_indicators(cls, v: List[str]) -> List[str]:
        """Validate indicators list."""
        valid_indicators = [
            "rsi",
            "rsi_14",
            "macd",
            "sma_20",
            "sma_50",
            "sma_200",
            "ema_12",
            "ema_26",
            "ema_50",
            "bbands",
            "stoch",
            "atr",
            "obv",
            "vwap",
        ]
        invalid = [ind for ind in v if ind not in valid_indicators]
        if invalid:
            raise ValueError(
                f"Invalid indicators: {', '.join(invalid)}. "
                f"Valid indicators: {', '.join(valid_indicators)}"
            )
        return v


class TickersListValidator(BaseModel):
    """Validator for tickers list input."""

    tickers: List[str] = Field(..., min_length=1)

    @field_validator("tickers")
    @classmethod
    def validate_tickers(cls, v: List[str]) -> List[str]:
        """Validate tickers list."""
        if len(v) > settings.MAX_TICKERS_PER_REQUEST:
            raise ValueError(
                f"Maximum {settings.MAX_TICKERS_PER_REQUEST} tickers per request"
            )
        return [t.upper().strip() for t in v if t.strip()]


class SearchQueryValidator(BaseModel):
    """Validator for search query input."""

    query: str = Field(..., min_length=1)
    limit: int = Field(default=10, ge=1, le=50)
    sector: Optional[str] = None

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate search query."""
        query = v.strip()
        if not query:
            raise ValueError("Query cannot be empty")
        return query


def validate_ticker(ticker: str) -> str:
    """Quick ticker validation."""
    validator = TickerValidator(ticker=ticker)
    return validator.ticker


def validate_period(period: str) -> str:
    """Quick period validation."""
    validator = PeriodValidator(period=period)
    return validator.period


def validate_interval(interval: str) -> str:
    """Quick interval validation."""
    validator = IntervalValidator(interval=interval)
    return validator.interval


def validate_indicators(indicators: List[str]) -> List[str]:
    """Quick indicators validation."""
    validator = IndicatorsValidator(indicators=indicators)
    return validator.indicators


def validate_tickers_list(tickers: List[str]) -> List[str]:
    """Quick tickers list validation."""
    validator = TickersListValidator(tickers=tickers)
    return validator.tickers

