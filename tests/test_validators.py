"""Tests for validators."""

import pytest
from src.utils.validators import (
    validate_ticker,
    validate_period,
    validate_interval,
    validate_indicators,
    validate_tickers_list,
    TickerValidator,
    PeriodValidator,
    IntervalValidator,
    IndicatorsValidator,
    TickersListValidator,
)


def test_validate_ticker():
    """Test ticker validation."""
    assert validate_ticker("BBCA") == "BBCA"
    assert validate_ticker("bbca") == "BBCA"
    
    with pytest.raises(ValueError):
        validate_ticker("")


def test_validate_period():
    """Test period validation."""
    assert validate_period("1mo") == "1mo"
    assert validate_period("1y") == "1y"
    
    with pytest.raises(ValueError):
        validate_period("invalid")


def test_validate_interval():
    """Test interval validation."""
    assert validate_interval("1d") == "1d"
    assert validate_interval("1wk") == "1wk"
    
    with pytest.raises(ValueError):
        validate_interval("invalid")


def test_validate_indicators():
    """Test indicators validation."""
    assert validate_indicators(["rsi", "macd"]) == ["rsi", "macd"]
    assert validate_indicators(["rsi_14", "sma_20"]) == ["rsi_14", "sma_20"]
    
    with pytest.raises(ValueError):
        validate_indicators(["invalid_indicator"])


def test_validate_tickers_list():
    """Test tickers list validation."""
    assert validate_tickers_list(["BBCA", "BBRI"]) == ["BBCA", "BBRI"]
    
    with pytest.raises(ValueError):
        validate_tickers_list([])


def test_ticker_validator():
    """Test TickerValidator."""
    validator = TickerValidator(ticker="BBCA")
    assert validator.ticker == "BBCA"


def test_period_validator():
    """Test PeriodValidator."""
    validator = PeriodValidator(period="1mo")
    assert validator.period == "1mo"


def test_interval_validator():
    """Test IntervalValidator."""
    validator = IntervalValidator(interval="1d")
    assert validator.interval == "1d"


def test_indicators_validator():
    """Test IndicatorsValidator."""
    validator = IndicatorsValidator(indicators=["rsi", "macd"])
    assert validator.indicators == ["rsi", "macd"]

