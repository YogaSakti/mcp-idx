"""Tests for helper functions."""

from src.utils.helpers import format_ticker, normalize_ticker, format_number


def test_format_ticker():
    """Test ticker formatting."""
    assert format_ticker("BBCA") == "BBCA.JK"
    assert format_ticker("BBCA.JK") == "BBCA.JK"
    assert format_ticker("bbca") == "BBCA.JK"


def test_normalize_ticker():
    """Test ticker normalization."""
    assert normalize_ticker("BBCA.JK") == "BBCA"
    assert normalize_ticker("BBCA") == "BBCA"
    assert normalize_ticker("bbca.jk") == "BBCA"


def test_format_number():
    """Test number formatting."""
    assert format_number(123.456789, 2) == 123.46
    assert format_number(123.456789, 0) == 123
    assert format_number(None, 2) is None
    assert format_number(100, 2) == 100.0

