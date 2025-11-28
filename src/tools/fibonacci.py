"""Tool for calculating Fibonacci retracement and extension levels."""

from typing import Any, Dict, List, Tuple
import pandas as pd
import numpy as np
from mcp.types import Tool
from src.utils.yahoo import yahoo_client, YahooFinanceError
from src.utils.validators import validate_ticker, validate_period


def get_fibonacci_levels_tool() -> Tool:
    """Get Fibonacci levels tool definition."""
    return Tool(
        name="get_fibonacci_levels",
        description="Menghitung Fibonacci retracement dan extension levels untuk support/resistance analysis.",
        inputSchema={
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Ticker saham IDX (contoh: BBCA, BBRI, TLKM)",
                },
                "period": {
                    "type": "string",
                    "description": "Periode data untuk analisis (1mo, 3mo, 6mo, 1y)",
                    "default": "3mo",
                },
                "trend": {
                    "type": "string",
                    "description": "Trend direction: 'auto' (detect otomatis), 'uptrend', atau 'downtrend'",
                    "enum": ["auto", "uptrend", "downtrend"],
                    "default": "auto",
                },
            },
            "required": ["ticker"],
        },
    )


def detect_swing_points(df: pd.DataFrame, window: int = 5) -> Tuple[float, float, int, int]:
    """
    Detect swing high and swing low points.

    Args:
        df: DataFrame with OHLCV data
        window: Window size for detecting swing points

    Returns:
        Tuple of (swing_high, swing_low, high_index, low_index)
    """
    high_prices = df['High'].values
    low_prices = df['Low'].values

    # Find the highest high and lowest low in the period
    swing_high_idx = np.argmax(high_prices)
    swing_low_idx = np.argmin(low_prices)

    swing_high = high_prices[swing_high_idx]
    swing_low = low_prices[swing_low_idx]

    return swing_high, swing_low, swing_high_idx, swing_low_idx


def calculate_fibonacci_levels(
    swing_high: float,
    swing_low: float,
    is_uptrend: bool
) -> Dict[str, float]:
    """
    Calculate Fibonacci retracement levels.

    Args:
        swing_high: Swing high price
        swing_low: Swing low price
        is_uptrend: True if uptrend, False if downtrend

    Returns:
        Dictionary of Fibonacci levels
    """
    diff = swing_high - swing_low

    # Fibonacci ratios
    fib_ratios = {
        "0.0%": 0.000,
        "23.6%": 0.236,
        "38.2%": 0.382,
        "50.0%": 0.500,
        "61.8%": 0.618,
        "78.6%": 0.786,
        "100.0%": 1.000,
    }

    levels = {}

    if is_uptrend:
        # For uptrend: retracement from high to low
        for label, ratio in fib_ratios.items():
            levels[label] = round(swing_high - (diff * ratio), 2)
    else:
        # For downtrend: retracement from low to high
        for label, ratio in fib_ratios.items():
            levels[label] = round(swing_low + (diff * ratio), 2)

    return levels


def calculate_fibonacci_extensions(
    swing_high: float,
    swing_low: float,
    is_uptrend: bool
) -> Dict[str, float]:
    """
    Calculate Fibonacci extension levels.

    Args:
        swing_high: Swing high price
        swing_low: Swing low price
        is_uptrend: True if uptrend, False if downtrend

    Returns:
        Dictionary of Fibonacci extension levels
    """
    diff = swing_high - swing_low

    # Extension ratios
    ext_ratios = {
        "127.2%": 1.272,
        "161.8%": 1.618,
        "200.0%": 2.000,
    }

    levels = {}

    if is_uptrend:
        # For uptrend: extensions above swing high
        for label, ratio in ext_ratios.items():
            levels[label] = round(swing_high + (diff * (ratio - 1)), 2)
    else:
        # For downtrend: extensions below swing low
        for label, ratio in ext_ratios.items():
            levels[label] = round(swing_low - (diff * (ratio - 1)), 2)

    return levels


def determine_trend(df: pd.DataFrame) -> bool:
    """
    Determine if the trend is uptrend or downtrend.

    Args:
        df: DataFrame with OHLCV data

    Returns:
        True if uptrend, False if downtrend
    """
    closes = df['Close'].values

    # Simple trend detection: compare first half vs second half
    mid_point = len(closes) // 2
    first_half_avg = np.mean(closes[:mid_point])
    second_half_avg = np.mean(closes[mid_point:])

    return second_half_avg > first_half_avg


def find_nearest_levels(
    current_price: float,
    retracement_levels: Dict[str, float]
) -> Tuple[str, float, str, float]:
    """
    Find nearest support and resistance levels.

    Args:
        current_price: Current stock price
        retracement_levels: Dictionary of Fibonacci levels

    Returns:
        Tuple of (support_label, support_level, resistance_label, resistance_level)
    """
    levels_list = [(label, level) for label, level in retracement_levels.items()]
    levels_list.sort(key=lambda x: x[1])  # Sort by price

    nearest_support = None
    nearest_resistance = None

    for label, level in levels_list:
        if level < current_price:
            nearest_support = (label, level)
        elif level > current_price and nearest_resistance is None:
            nearest_resistance = (label, level)
            break

    # Default values if not found
    if nearest_support is None:
        nearest_support = ("N/A", 0)
    if nearest_resistance is None:
        nearest_resistance = ("N/A", 0)

    return (
        nearest_support[0],
        nearest_support[1],
        nearest_resistance[0],
        nearest_resistance[1]
    )


async def get_fibonacci_levels(args: dict[str, Any]) -> dict[str, Any]:
    """
    Calculate Fibonacci retracement and extension levels.

    Args:
        args: Dictionary with 'ticker', optional 'period' and 'trend'

    Returns:
        Dictionary with Fibonacci levels and analysis
    """
    try:
        ticker = validate_ticker(args.get("ticker", ""))
        period = validate_period(args.get("period", "3mo"))
        trend_param = args.get("trend", "auto")

        # Get historical data
        hist_data = yahoo_client.get_historical_data(ticker, period=period, interval="1d")
        if "error" in hist_data:
            return hist_data

        # Convert to DataFrame
        df_data = hist_data["data"]
        df = pd.DataFrame(df_data)
        df["Date"] = pd.to_datetime(df["date"])
        df.set_index("Date", inplace=True)

        # Rename columns
        df.rename(columns={
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume"
        }, inplace=True)

        # Get current price
        price_data = yahoo_client.get_current_price(ticker)
        current_price = price_data.get("price", 0)

        # Detect swing points
        swing_high, swing_low, high_idx, low_idx = detect_swing_points(df)

        # Determine trend
        if trend_param == "auto":
            is_uptrend = determine_trend(df)
            trend_direction = "uptrend" if is_uptrend else "downtrend"
        else:
            is_uptrend = trend_param == "uptrend"
            trend_direction = trend_param

        # Calculate Fibonacci levels
        retracement_levels = calculate_fibonacci_levels(swing_high, swing_low, is_uptrend)
        extension_levels = calculate_fibonacci_extensions(swing_high, swing_low, is_uptrend)

        # Find nearest support/resistance
        support_label, support_level, resistance_label, resistance_level = find_nearest_levels(
            current_price, retracement_levels
        )

        # Determine current position
        position_description = f"Between {support_label} and {resistance_label}"
        if support_label == "N/A":
            position_description = f"Below {resistance_label}"
        elif resistance_label == "N/A":
            position_description = f"Above {support_label}"

        # Calculate risk/reward ratio for potential trade
        if support_level > 0 and resistance_level > 0:
            potential_reward = resistance_level - current_price
            potential_risk = current_price - support_level
            risk_reward_ratio = round(potential_reward / potential_risk, 2) if potential_risk > 0 else 0
        else:
            risk_reward_ratio = 0

        result = {
            "ticker": ticker,
            "period": period,
            "current_price": current_price,
            "trend": trend_direction,
            "swing_high": round(swing_high, 2),
            "swing_low": round(swing_low, 2),
            "price_range": round(swing_high - swing_low, 2),
            "retracement_levels": retracement_levels,
            "extension_levels": extension_levels,
            "nearest_support": {
                "level": support_label,
                "price": support_level
            },
            "nearest_resistance": {
                "level": resistance_label,
                "price": resistance_level
            },
            "current_position": position_description,
            "risk_reward_ratio": risk_reward_ratio,
        }

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
        }
    except Exception as e:
        return {
            "error": True,
            "code": "NETWORK_ERROR",
            "message": f"Gagal menghitung Fibonacci levels: {str(e)}",
        }
