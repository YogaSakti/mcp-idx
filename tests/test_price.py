"""Tests for price tool."""

import pytest
from src.tools.price import get_stock_price
from src.utils.validators import validate_ticker


@pytest.mark.asyncio
async def test_get_stock_price_valid_ticker():
    """Test getting price for valid ticker."""
    result = await get_stock_price({"ticker": "BBCA"})
    assert "error" not in result or result.get("error") is False
    assert "ticker" in result
    assert "price" in result


@pytest.mark.asyncio
async def test_get_stock_price_invalid_ticker():
    """Test getting price for invalid ticker."""
    result = await get_stock_price({"ticker": "INVALID123"})
    # Should return error or handle gracefully
    assert isinstance(result, dict)


def test_validate_ticker():
    """Test ticker validation."""
    assert validate_ticker("BBCA") == "BBCA"
    assert validate_ticker("bbca") == "BBCA"
    assert validate_ticker("BBCA.JK") == "BBCA.JK"

