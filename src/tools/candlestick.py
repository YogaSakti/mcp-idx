"""Candlestick pattern recognition tool for Indonesian stocks."""

from typing import Any, Dict, List, Optional
from mcp.types import Tool
import pandas as pd
import numpy as np

from src.utils.yahoo import yahoo_client, YahooFinanceError
from src.utils.validators import validate_ticker, validate_period


def get_candlestick_patterns_tool() -> Tool:
    """Return the MCP tool definition for candlestick pattern detection."""
    return Tool(
        name="get_candlestick_patterns",
        description=(
            "Detect candlestick patterns (Doji, Hammer, Shooting Star, Engulfing, etc.) "
            "untuk Indonesian stocks. Returns detected patterns dengan bullish/bearish signals."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Stock ticker (e.g., BBCA.JK, BBRI.JK)",
                },
                "period": {
                    "type": "string",
                    "description": "Data period: 1mo, 3mo, 6mo (default: 1mo)",
                    "default": "1mo",
                },
                "lookback_days": {
                    "type": "integer",
                    "description": "Days to look back for patterns (default: 10)",
                    "default": 10,
                },
            },
            "required": ["ticker"],
        },
    )


def is_doji(open_price: float, close: float, high: float, low: float, body_threshold: float = 0.1) -> bool:
    """
    Detect Doji pattern.

    Doji: Open ≈ Close, indicating indecision
    """
    body = abs(close - open_price)
    total_range = high - low

    if total_range == 0:
        return False

    # Body is very small compared to total range
    return (body / total_range) < body_threshold


def is_hammer(open_price: float, close: float, high: float, low: float) -> bool:
    """
    Detect Hammer pattern (Bullish reversal).

    Hammer: Small body at top, long lower shadow (2x body), short upper shadow
    """
    body = abs(close - open_price)
    upper_shadow = high - max(open_price, close)
    lower_shadow = min(open_price, close) - low

    if body == 0:
        return False

    # Long lower shadow (at least 2x body), short upper shadow
    return lower_shadow >= 2 * body and upper_shadow < body


def is_shooting_star(open_price: float, close: float, high: float, low: float) -> bool:
    """
    Detect Shooting Star pattern (Bearish reversal).

    Shooting Star: Small body at bottom, long upper shadow (2x body), short lower shadow
    """
    body = abs(close - open_price)
    upper_shadow = high - max(open_price, close)
    lower_shadow = min(open_price, close) - low

    if body == 0:
        return False

    # Long upper shadow (at least 2x body), short lower shadow
    return upper_shadow >= 2 * body and lower_shadow < body


def is_bullish_engulfing(
    prev_open: float, prev_close: float,
    curr_open: float, curr_close: float
) -> bool:
    """
    Detect Bullish Engulfing pattern.

    Previous candle: Bearish (red)
    Current candle: Bullish (green) that engulfs previous body
    """
    # Previous candle is bearish
    prev_bearish = prev_close < prev_open
    # Current candle is bullish
    curr_bullish = curr_close > curr_open

    if not (prev_bearish and curr_bullish):
        return False

    # Current body engulfs previous body
    return curr_open <= prev_close and curr_close >= prev_open


def is_bearish_engulfing(
    prev_open: float, prev_close: float,
    curr_open: float, curr_close: float
) -> bool:
    """
    Detect Bearish Engulfing pattern.

    Previous candle: Bullish (green)
    Current candle: Bearish (red) that engulfs previous body
    """
    # Previous candle is bullish
    prev_bullish = prev_close > prev_open
    # Current candle is bearish
    curr_bearish = curr_close < curr_open

    if not (prev_bullish and curr_bearish):
        return False

    # Current body engulfs previous body
    return curr_open >= prev_close and curr_close <= prev_open


def is_morning_star(
    day1_open: float, day1_close: float,
    day2_open: float, day2_close: float, day2_high: float, day2_low: float,
    day3_open: float, day3_close: float
) -> bool:
    """
    Detect Morning Star pattern (Bullish reversal).

    Day 1: Long bearish candle
    Day 2: Small body (star) - doji or small candle
    Day 3: Long bullish candle
    """
    # Day 1: Bearish
    day1_bearish = day1_close < day1_open
    day1_body = abs(day1_close - day1_open)

    # Day 2: Small body (doji-like)
    day2_body = abs(day2_close - day2_open)
    day2_small = day2_body < day1_body * 0.3

    # Day 3: Bullish
    day3_bullish = day3_close > day3_open
    day3_body = abs(day3_close - day3_open)

    # Day 3 closes above middle of Day 1
    return (day1_bearish and day2_small and day3_bullish and
            day3_close > (day1_open + day1_close) / 2)


def is_evening_star(
    day1_open: float, day1_close: float,
    day2_open: float, day2_close: float, day2_high: float, day2_low: float,
    day3_open: float, day3_close: float
) -> bool:
    """
    Detect Evening Star pattern (Bearish reversal).

    Day 1: Long bullish candle
    Day 2: Small body (star)
    Day 3: Long bearish candle
    """
    # Day 1: Bullish
    day1_bullish = day1_close > day1_open
    day1_body = abs(day1_close - day1_open)

    # Day 2: Small body
    day2_body = abs(day2_close - day2_open)
    day2_small = day2_body < day1_body * 0.3

    # Day 3: Bearish
    day3_bearish = day3_close < day3_open
    day3_body = abs(day3_close - day3_open)

    # Day 3 closes below middle of Day 1
    return (day1_bullish and day2_small and day3_bearish and
            day3_close < (day1_open + day1_close) / 2)


def detect_patterns(df: pd.DataFrame, lookback_days: int = 10) -> List[Dict[str, Any]]:
    """
    Detect all candlestick patterns in recent data.

    Args:
        df: DataFrame with OHLC data
        lookback_days: Number of days to look back

    Returns:
        List of detected patterns
    """
    patterns = []

    # Only look at recent data
    df_recent = df.tail(lookback_days + 3)  # +3 for 3-day patterns

    for i in range(2, len(df_recent)):
        date = df_recent.index[i]
        curr = df_recent.iloc[i]
        prev = df_recent.iloc[i-1] if i > 0 else None
        prev2 = df_recent.iloc[i-2] if i > 1 else None

        # Single candle patterns
        if is_doji(curr['Open'], curr['Close'], curr['High'], curr['Low']):
            patterns.append({
                "pattern": "Doji",
                "type": "indecision",
                "date": date.strftime("%Y-%m-%d"),
                "signal": "neutral",
                "strength": "medium",
                "description": "Indecision - potential reversal"
            })

        if is_hammer(curr['Open'], curr['Close'], curr['High'], curr['Low']):
            patterns.append({
                "pattern": "Hammer",
                "type": "reversal",
                "date": date.strftime("%Y-%m-%d"),
                "signal": "bullish",
                "strength": "strong",
                "description": "Bullish reversal signal"
            })

        if is_shooting_star(curr['Open'], curr['Close'], curr['High'], curr['Low']):
            patterns.append({
                "pattern": "Shooting Star",
                "type": "reversal",
                "date": date.strftime("%Y-%m-%d"),
                "signal": "bearish",
                "strength": "strong",
                "description": "Bearish reversal signal"
            })

        # Two candle patterns
        if prev is not None:
            if is_bullish_engulfing(prev['Open'], prev['Close'], curr['Open'], curr['Close']):
                patterns.append({
                    "pattern": "Bullish Engulfing",
                    "type": "reversal",
                    "date": date.strftime("%Y-%m-%d"),
                    "signal": "bullish",
                    "strength": "very_strong",
                    "description": "Strong bullish reversal - buyers overwhelming sellers"
                })

            if is_bearish_engulfing(prev['Open'], prev['Close'], curr['Open'], curr['Close']):
                patterns.append({
                    "pattern": "Bearish Engulfing",
                    "type": "reversal",
                    "date": date.strftime("%Y-%m-%d"),
                    "signal": "bearish",
                    "strength": "very_strong",
                    "description": "Strong bearish reversal - sellers overwhelming buyers"
                })

        # Three candle patterns
        if prev is not None and prev2 is not None:
            if is_morning_star(
                prev2['Open'], prev2['Close'],
                prev['Open'], prev['Close'], prev['High'], prev['Low'],
                curr['Open'], curr['Close']
            ):
                patterns.append({
                    "pattern": "Morning Star",
                    "type": "reversal",
                    "date": date.strftime("%Y-%m-%d"),
                    "signal": "bullish",
                    "strength": "very_strong",
                    "description": "Strong bullish reversal - trend change likely"
                })

            if is_evening_star(
                prev2['Open'], prev2['Close'],
                prev['Open'], prev['Close'], prev['High'], prev['Low'],
                curr['Open'], curr['Close']
            ):
                patterns.append({
                    "pattern": "Evening Star",
                    "type": "reversal",
                    "date": date.strftime("%Y-%m-%d"),
                    "signal": "bearish",
                    "strength": "very_strong",
                    "description": "Strong bearish reversal - trend change likely"
                })

    return patterns


async def get_candlestick_patterns(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect candlestick patterns for a stock.

    Args:
        args: Dictionary containing:
            - ticker: Stock ticker
            - period: Data period (default: 1mo)
            - lookback_days: Days to look back (default: 10)

    Returns:
        Dictionary containing pattern information
    """
    ticker = args.get("ticker", "").upper()
    period = args.get("period", "1mo")
    lookback_days = args.get("lookback_days", 10)

    if not ticker:
        return {"error": "Ticker is required"}

    try:
        # Validate inputs
        ticker = validate_ticker(ticker)
        period = validate_period(period)

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

        if df.empty:
            return {
                "ticker": ticker,
                "error": "No data available",
            }

        # Detect patterns
        patterns = detect_patterns(df, lookback_days)

        result = {
            "ticker": ticker,
            "period": period,
            "lookback_days": lookback_days,
            "current_price": round(float(df['Close'].iloc[-1]), 2),
            "patterns_detected": len(patterns),
            "patterns": patterns,
        }

        # Group by signal
        bullish_patterns = [p for p in patterns if p["signal"] == "bullish"]
        bearish_patterns = [p for p in patterns if p["signal"] == "bearish"]
        neutral_patterns = [p for p in patterns if p["signal"] == "neutral"]

        result["summary"] = {
            "bullish_count": len(bullish_patterns),
            "bearish_count": len(bearish_patterns),
            "neutral_count": len(neutral_patterns),
        }

        # Trading insights
        insights = []
        if bullish_patterns:
            latest = bullish_patterns[-1]
            insights.append(f"🟢 {latest['pattern']} detected on {latest['date']} - {latest['description']}")
        if bearish_patterns:
            latest = bearish_patterns[-1]
            insights.append(f"🔴 {latest['pattern']} detected on {latest['date']} - {latest['description']}")
        if neutral_patterns:
            latest = neutral_patterns[-1]
            insights.append(f"🟡 {latest['pattern']} detected on {latest['date']} - {latest['description']}")

        if not patterns:
            insights.append("No significant candlestick patterns detected in the lookback period")

        result["insights"] = insights

        return result

    except Exception as e:
        return {
            "ticker": ticker,
            "error": str(e),
        }
