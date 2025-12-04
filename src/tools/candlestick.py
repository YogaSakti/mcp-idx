"""
Candlestick pattern recognition tool for Indonesian stocks.
OPTIMIZED FOR IDX MARKET dengan trend context dan volume confirmation.
"""

from typing import Any, Dict, List, Optional, Tuple
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
            "Detect candlestick patterns (Doji, Hammer, Shooting Star, Engulfing, Marubozu, etc.) "
            "untuk Indonesian stocks. Includes trend context validation dan volume confirmation. "
            "Returns detected patterns dengan bullish/bearish signals dan validity score."
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


# =============================================================================
# TREND DETECTION - Critical for pattern validity
# =============================================================================

def detect_short_term_trend(df: pd.DataFrame, current_idx: int, lookback: int = 5) -> str:
    """
    Detect short-term trend before current candle.
    
    Args:
        df: DataFrame with OHLC data
        current_idx: Current position index
        lookback: Number of days to look back for trend
        
    Returns:
        "uptrend", "downtrend", or "sideways"
    """
    if current_idx < lookback:
        return "unknown"
    
    # Get recent closes before current candle
    start_idx = max(0, current_idx - lookback)
    recent_closes = df['Close'].iloc[start_idx:current_idx]
    
    if len(recent_closes) < 2:
        return "unknown"
    
    # Calculate trend based on price change and slope
    price_change_pct = (recent_closes.iloc[-1] - recent_closes.iloc[0]) / recent_closes.iloc[0] * 100
    
    # Also check MA slope
    if len(recent_closes) >= 3:
        ma = recent_closes.rolling(min(5, len(recent_closes)), min_periods=2).mean()
        ma_slope = (ma.iloc[-1] - ma.iloc[-2]) / ma.iloc[-2] * 100 if ma.iloc[-2] != 0 else 0
    else:
        ma_slope = 0
    
    # Threshold for trend detection
    if price_change_pct > 2 or ma_slope > 0.5:
        return "uptrend"
    elif price_change_pct < -2 or ma_slope < -0.5:
        return "downtrend"
    else:
        return "sideways"


def get_price_vs_ma(df: pd.DataFrame, current_idx: int, ma_period: int = 20) -> Tuple[str, float]:
    """
    Get price position relative to MA.
    
    Returns:
        Tuple of (position: "above"/"below"/"at", distance_pct: float)
    """
    if current_idx < ma_period:
        return "unknown", 0.0
    
    ma = df['Close'].iloc[max(0, current_idx - ma_period):current_idx].mean()
    current_close = df['Close'].iloc[current_idx]
    
    if ma == 0:
        return "unknown", 0.0
    
    distance_pct = (current_close - ma) / ma * 100
    
    if distance_pct > 1:
        return "above", distance_pct
    elif distance_pct < -1:
        return "below", distance_pct
    else:
        return "at", distance_pct


# =============================================================================
# PATTERN DETECTION FUNCTIONS
# =============================================================================

def get_adaptive_doji_threshold(price: float) -> float:
    """
    Get adaptive doji threshold based on price level.
    For gocap (low price stocks), tick size makes body appear smaller.
    
    Args:
        price: Current stock price
        
    Returns:
        Appropriate doji threshold
    """
    if price < 100:
        return 0.20  # More lenient for gocap (tick = 1)
    elif price < 200:
        return 0.15  # Tick = 1
    elif price < 500:
        return 0.12  # Tick = 2
    else:
        return 0.10  # Standard threshold


def is_doji(open_price: float, close: float, high: float, low: float, 
            body_threshold: float = None) -> bool:
    """
    Detect Doji pattern with adaptive threshold.

    Doji: Open ≈ Close, indicating indecision
    """
    body = abs(close - open_price)
    total_range = high - low

    if total_range == 0:
        return False
    
    # Use adaptive threshold if not provided
    if body_threshold is None:
        body_threshold = get_adaptive_doji_threshold(close)

    # Body is very small compared to total range
    return (body / total_range) < body_threshold


def is_hammer(open_price: float, close: float, high: float, low: float) -> bool:
    """
    Detect Hammer pattern shape.
    NOTE: Validity depends on trend context (should be after downtrend).

    Hammer: Small body at top, long lower shadow (2x body), short upper shadow
    """
    body = abs(close - open_price)
    upper_shadow = high - max(open_price, close)
    lower_shadow = min(open_price, close) - low

    if body == 0:
        body = 0.01  # Prevent division by zero, treat as very small body
        
    total_range = high - low
    if total_range == 0:
        return False

    # Long lower shadow (at least 2x body), short upper shadow
    return lower_shadow >= 2 * body and upper_shadow < body


def is_inverted_hammer(open_price: float, close: float, high: float, low: float) -> bool:
    """
    Detect Inverted Hammer pattern (Bullish reversal at bottom).
    Similar shape to shooting star but at bottom of downtrend.
    """
    body = abs(close - open_price)
    upper_shadow = high - max(open_price, close)
    lower_shadow = min(open_price, close) - low

    if body == 0:
        body = 0.01
        
    total_range = high - low
    if total_range == 0:
        return False

    # Long upper shadow (at least 2x body), short lower shadow
    # Same shape as shooting star, but meaning depends on trend
    return upper_shadow >= 2 * body and lower_shadow < body


def is_shooting_star(open_price: float, close: float, high: float, low: float) -> bool:
    """
    Detect Shooting Star pattern shape.
    NOTE: Validity depends on trend context (should be after uptrend).

    Shooting Star: Small body at bottom, long upper shadow (2x body), short lower shadow
    """
    body = abs(close - open_price)
    upper_shadow = high - max(open_price, close)
    lower_shadow = min(open_price, close) - low

    if body == 0:
        body = 0.01
        
    total_range = high - low
    if total_range == 0:
        return False

    # Long upper shadow (at least 2x body), short lower shadow
    return upper_shadow >= 2 * body and lower_shadow < body


def is_hanging_man(open_price: float, close: float, high: float, low: float) -> bool:
    """
    Detect Hanging Man pattern (Bearish reversal at top).
    Same shape as Hammer but at top of uptrend.
    """
    # Same shape as hammer
    return is_hammer(open_price, close, high, low)


def is_marubozu(open_price: float, close: float, high: float, low: float, 
               shadow_threshold: float = 0.02) -> Tuple[bool, Optional[str]]:
    """
    Detect Marubozu pattern (Full body candle with minimal shadows).
    IMPORTANT for IDX: Often appears during ARA (Auto Reject Atas).
    
    Args:
        open_price, close, high, low: OHLC data
        shadow_threshold: Max shadow size as fraction of body
        
    Returns:
        Tuple of (is_marubozu: bool, direction: "bullish"/"bearish"/None)
    """
    body = abs(close - open_price)
    upper_shadow = high - max(open_price, close)
    lower_shadow = min(open_price, close) - low
    
    if body == 0:
        return False, None
    
    # Shadows must be very small compared to body
    small_shadows = upper_shadow < body * shadow_threshold and lower_shadow < body * shadow_threshold
    
    if small_shadows:
        direction = "bullish" if close > open_price else "bearish"
        return True, direction
    
    return False, None


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
    
    # Guard: if Day 1 body is 0 (doji), pattern is not valid
    if day1_body == 0:
        return False

    # Day 2: Small body (doji-like)
    day2_body = abs(day2_close - day2_open)
    day2_small = day2_body < day1_body * 0.3

    # Day 3: Bullish
    day3_bullish = day3_close > day3_open

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
    
    # Guard: if Day 1 body is 0 (doji), pattern is not valid
    if day1_body == 0:
        return False

    # Day 2: Small body
    day2_body = abs(day2_close - day2_open)
    day2_small = day2_body < day1_body * 0.3

    # Day 3: Bearish
    day3_bearish = day3_close < day3_open

    # Day 3 closes below middle of Day 1
    return (day1_bullish and day2_small and day3_bearish and
            day3_close < (day1_open + day1_close) / 2)


# =============================================================================
# MAIN DETECTION FUNCTION
# =============================================================================

def detect_patterns(df: pd.DataFrame, lookback_days: int = 10) -> List[Dict[str, Any]]:
    """
    Detect all candlestick patterns in recent data WITH TREND CONTEXT.
    IDX-optimized: Only marks patterns as valid if trend context is correct.

    Args:
        df: DataFrame with OHLC data (must be sorted ascending by date)
        lookback_days: Number of days to look back

    Returns:
        List of detected patterns with validity info
    """
    patterns = []
    
    # Ensure we have enough data
    if len(df) < lookback_days + 5:
        return patterns

    # Calculate volume MA for confirmation
    df['Volume_MA'] = df['Volume'].rolling(20, min_periods=5).mean()
    
    # Get indices for lookback period
    # We want to analyze the last `lookback_days` candles
    start_idx = len(df) - lookback_days
    
    for i in range(max(start_idx, 3), len(df)):  # Start from 3 to have prev/prev2
        date = df.index[i]
        curr = df.iloc[i]
        prev = df.iloc[i-1]
        prev2 = df.iloc[i-2]
        
        # Get trend context
        trend = detect_short_term_trend(df, i, lookback=5)
        price_pos, price_dist = get_price_vs_ma(df, i, ma_period=20)
        
        # Volume confirmation (convert to Python bool for JSON serialization)
        vol_ma = df['Volume_MA'].iloc[i] if pd.notna(df['Volume_MA'].iloc[i]) else df['Volume'].iloc[i]
        vol_ma_float = float(vol_ma) if pd.notna(vol_ma) else 0.0
        curr_vol = float(curr['Volume']) if pd.notna(curr['Volume']) else 0.0
        
        if vol_ma_float > 0:
            has_volume = bool(curr_vol > vol_ma_float * 1.0)
            has_high_volume = bool(curr_vol > vol_ma_float * 1.5)
        else:
            has_volume = True
            has_high_volume = False
        
        # =====================================================================
        # SINGLE CANDLE PATTERNS
        # =====================================================================
        
        # DOJI - Indecision (valid in any trend)
        if is_doji(curr['Open'], curr['Close'], curr['High'], curr['Low']):
            patterns.append({
                "pattern": "Doji",
                "type": "indecision",
                "date": date.strftime("%Y-%m-%d"),
                "signal": "neutral",
                "strength": "medium",
                "trend_context": trend,
                "is_valid": True,  # Doji always valid as warning
                "volume_confirmed": has_volume,
                "description": "Indecision candle - potential reversal or pause"
            })
        
        # MARUBOZU - Strong momentum (important for IDX ARA)
        is_maru, maru_dir = is_marubozu(curr['Open'], curr['Close'], curr['High'], curr['Low'])
        if is_maru:
            is_valid = True  # Marubozu valid in any context, it's momentum
            strength = "very_strong" if has_high_volume else "strong"
            
            # Check if could be ARA candidate
            price_change = (curr['Close'] - prev['Close']) / prev['Close'] * 100 if prev['Close'] > 0 else 0
            is_potential_ara = bool(maru_dir == "bullish" and price_change > 15)
            
            patterns.append({
                "pattern": "Marubozu",
                "type": "momentum",
                "date": date.strftime("%Y-%m-%d"),
                "signal": maru_dir,
                "strength": strength,
                "trend_context": trend,
                "is_valid": is_valid,
                "volume_confirmed": has_volume,
                "potential_ara": is_potential_ara,
                "description": f"{'Bullish' if maru_dir == 'bullish' else 'Bearish'} Marubozu - Strong {maru_dir} momentum" + 
                              (" (potential ARA)" if is_potential_ara else "")
            })
        
        # =====================================================================
        # HAMMER SHAPE PATTERNS (long lower shadow)
        # Same shape, different meaning based on trend:
        # - Downtrend → Hammer (bullish reversal)
        # - Uptrend → Hanging Man (bearish reversal)
        # =====================================================================
        has_hammer_shape = is_hammer(curr['Open'], curr['Close'], curr['High'], curr['Low'])
        
        if has_hammer_shape:
            if trend == "downtrend" or price_pos == "below":
                # HAMMER - Bullish reversal at bottom
                patterns.append({
                    "pattern": "Hammer",
                    "type": "reversal",
                    "date": date.strftime("%Y-%m-%d"),
                    "signal": "bullish",
                    "strength": "strong" if has_volume else "medium",
                    "trend_context": trend,
                    "price_vs_ma": price_pos,
                    "is_valid": True,
                    "volume_confirmed": has_volume,
                    "description": "Bullish reversal signal ✓ Valid (after downtrend)"
                })
            elif trend == "uptrend" or price_pos == "above":
                # HANGING MAN - Bearish reversal at top
                patterns.append({
                    "pattern": "Hanging Man",
                    "type": "reversal",
                    "date": date.strftime("%Y-%m-%d"),
                    "signal": "bearish",
                    "strength": "strong" if has_volume else "medium",
                    "trend_context": trend,
                    "price_vs_ma": price_pos,
                    "is_valid": True,
                    "volume_confirmed": has_volume,
                    "description": "Bearish reversal at top - warning sign ✓"
                })
            else:
                # Sideways - pattern is weak/neutral
                patterns.append({
                    "pattern": "Hammer (Neutral)",
                    "type": "indecision",
                    "date": date.strftime("%Y-%m-%d"),
                    "signal": "neutral",
                    "strength": "weak",
                    "trend_context": trend,
                    "price_vs_ma": price_pos,
                    "is_valid": False,
                    "volume_confirmed": has_volume,
                    "description": "Hammer shape in sideways - no clear signal ⚠️"
                })
        
        # =====================================================================
        # SHOOTING STAR SHAPE PATTERNS (long upper shadow)
        # Same shape, different meaning based on trend:
        # - Uptrend → Shooting Star (bearish reversal)
        # - Downtrend → Inverted Hammer (bullish reversal)
        # =====================================================================
        has_shooting_star_shape = is_shooting_star(curr['Open'], curr['Close'], curr['High'], curr['Low'])
        
        if has_shooting_star_shape:
            if trend == "uptrend" or price_pos == "above":
                # SHOOTING STAR - Bearish reversal at top
                patterns.append({
                    "pattern": "Shooting Star",
                    "type": "reversal",
                    "date": date.strftime("%Y-%m-%d"),
                    "signal": "bearish",
                    "strength": "strong" if has_volume else "medium",
                    "trend_context": trend,
                    "price_vs_ma": price_pos,
                    "is_valid": True,
                    "volume_confirmed": has_volume,
                    "description": "Bearish reversal signal ✓ Valid (after uptrend)"
                })
            elif trend == "downtrend" or price_pos == "below":
                # INVERTED HAMMER - Bullish reversal at bottom
                patterns.append({
                    "pattern": "Inverted Hammer",
                    "type": "reversal",
                    "date": date.strftime("%Y-%m-%d"),
                    "signal": "bullish",
                    "strength": "strong" if has_volume else "medium",
                    "trend_context": trend,
                    "price_vs_ma": price_pos,
                    "is_valid": True,
                    "volume_confirmed": has_volume,
                    "description": "Bullish reversal at bottom ✓"
                })
            else:
                # Sideways - pattern is weak/neutral
                patterns.append({
                    "pattern": "Upper Shadow Star (Neutral)",
                    "type": "indecision",
                    "date": date.strftime("%Y-%m-%d"),
                    "signal": "neutral",
                    "strength": "weak",
                    "trend_context": trend,
                    "price_vs_ma": price_pos,
                    "is_valid": False,
                    "volume_confirmed": has_volume,
                    "description": "Upper shadow pattern in sideways - no clear signal ⚠️"
                })
        
        # =====================================================================
        # TWO CANDLE PATTERNS
        # =====================================================================
        
        # BULLISH ENGULFING
        if is_bullish_engulfing(prev['Open'], prev['Close'], curr['Open'], curr['Close']):
            is_valid = bool(trend == "downtrend" or price_pos in ["below", "at"])
            strength = "very_strong" if is_valid and has_high_volume else "strong" if is_valid else "medium"
            
            patterns.append({
                "pattern": "Bullish Engulfing",
                "type": "reversal",
                "date": date.strftime("%Y-%m-%d"),
                "signal": "bullish",
                "strength": strength,
                "trend_context": trend,
                "price_vs_ma": price_pos,
                "is_valid": is_valid,
                "volume_confirmed": has_volume,
                "description": "Strong bullish reversal - buyers overwhelming sellers" +
                              (" ✓" if is_valid else " ⚠️ Context weak")
            })

        # BEARISH ENGULFING
        if is_bearish_engulfing(prev['Open'], prev['Close'], curr['Open'], curr['Close']):
            is_valid = bool(trend == "uptrend" or price_pos in ["above", "at"])
            strength = "very_strong" if is_valid and has_high_volume else "strong" if is_valid else "medium"
            
            patterns.append({
                "pattern": "Bearish Engulfing",
                "type": "reversal",
                "date": date.strftime("%Y-%m-%d"),
                "signal": "bearish",
                "strength": strength,
                "trend_context": trend,
                "price_vs_ma": price_pos,
                "is_valid": is_valid,
                "volume_confirmed": has_volume,
                "description": "Strong bearish reversal - sellers overwhelming buyers" +
                              (" ✓" if is_valid else " ⚠️ Context weak")
            })

        # =====================================================================
        # THREE CANDLE PATTERNS
        # =====================================================================
        
        # MORNING STAR - Bullish reversal
        if is_morning_star(
            prev2['Open'], prev2['Close'],
            prev['Open'], prev['Close'], prev['High'], prev['Low'],
            curr['Open'], curr['Close']
        ):
            is_valid = bool(trend == "downtrend" or price_pos == "below")
            strength = "very_strong" if is_valid else "strong"
            
            patterns.append({
                "pattern": "Morning Star",
                "type": "reversal",
                "date": date.strftime("%Y-%m-%d"),
                "signal": "bullish",
                "strength": strength,
                "trend_context": trend,
                "price_vs_ma": price_pos,
                "is_valid": is_valid,
                "volume_confirmed": has_volume,
                "description": "Strong bullish reversal - trend change likely" +
                              (" ✓" if is_valid else " ⚠️")
            })

        # EVENING STAR - Bearish reversal
        if is_evening_star(
            prev2['Open'], prev2['Close'],
            prev['Open'], prev['Close'], prev['High'], prev['Low'],
            curr['Open'], curr['Close']
        ):
            is_valid = bool(trend == "uptrend" or price_pos == "above")
            strength = "very_strong" if is_valid else "strong"
            
            patterns.append({
                "pattern": "Evening Star",
                "type": "reversal",
                "date": date.strftime("%Y-%m-%d"),
                "signal": "bearish",
                "strength": strength,
                "trend_context": trend,
                "price_vs_ma": price_pos,
                "is_valid": is_valid,
                "volume_confirmed": has_volume,
                "description": "Strong bearish reversal - trend change likely" +
                              (" ✓" if is_valid else " ⚠️")
            })

    return patterns


# =============================================================================
# MAIN ASYNC HANDLER
# =============================================================================

async def get_candlestick_patterns(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect candlestick patterns for a stock with IDX optimizations.

    Args:
        args: Dictionary containing:
            - ticker: Stock ticker
            - period: Data period (default: 1mo)
            - lookback_days: Days to look back (default: 10)

    Returns:
        Dictionary containing pattern information with validity scores
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

        # CRITICAL: Sort by date ascending for correct pattern detection
        df.sort_index(inplace=True)

        # Rename columns
        df.rename(columns={
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume"
        }, inplace=True)
        
        # Ensure numeric types
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Drop rows with NaN values
        df.dropna(subset=['Open', 'High', 'Low', 'Close'], inplace=True)

        if df.empty:
            return {
                "ticker": ticker,
                "error": "No data available",
            }

        # Detect patterns
        patterns = detect_patterns(df, lookback_days)

        # Separate valid and invalid patterns
        valid_patterns = [p for p in patterns if p.get("is_valid", True)]
        weak_patterns = [p for p in patterns if not p.get("is_valid", True)]

        result = {
            "ticker": ticker,
            "period": period,
            "lookback_days": lookback_days,
            "current_price": round(float(df['Close'].iloc[-1]), 2),
            "data_points": len(df),
            "patterns_detected": len(patterns),
            "valid_patterns_count": len(valid_patterns),
            "weak_patterns_count": len(weak_patterns),
            "patterns": patterns,
        }

        # Group by signal (only valid patterns)
        bullish_valid = [p for p in valid_patterns if p["signal"] == "bullish"]
        bearish_valid = [p for p in valid_patterns if p["signal"] == "bearish"]
        neutral_patterns = [p for p in patterns if p["signal"] == "neutral"]

        result["summary"] = {
            "bullish_valid": len(bullish_valid),
            "bearish_valid": len(bearish_valid),
            "neutral_count": len(neutral_patterns),
            "total_valid": len(valid_patterns),
            "total_weak": len(weak_patterns),
        }
        
        # Volume confirmation stats
        vol_confirmed = len([p for p in valid_patterns if p.get("volume_confirmed", False)])
        result["volume_confirmation"] = {
            "confirmed_count": vol_confirmed,
            "confirmation_rate": round(vol_confirmed / len(valid_patterns) * 100, 1) if valid_patterns else 0
        }

        # Trading insights (prioritize valid patterns)
        insights = []
        
        # Check for ARA potential
        ara_patterns = [p for p in patterns if p.get("potential_ara", False)]
        if ara_patterns:
            latest = ara_patterns[-1]
            insights.append(f"🚀 POTENTIAL ARA: {latest['pattern']} on {latest['date']} - Strong bullish momentum!")
        
        if bullish_valid:
            latest = bullish_valid[-1]
            vol_note = " (volume confirmed)" if latest.get("volume_confirmed") else ""
            insights.append(f"🟢 VALID: {latest['pattern']} on {latest['date']} - {latest['description']}{vol_note}")
            
        if bearish_valid:
            latest = bearish_valid[-1]
            vol_note = " (volume confirmed)" if latest.get("volume_confirmed") else ""
            insights.append(f"🔴 VALID: {latest['pattern']} on {latest['date']} - {latest['description']}{vol_note}")
            
        if neutral_patterns:
            latest = neutral_patterns[-1]
            insights.append(f"🟡 {latest['pattern']} on {latest['date']} - {latest['description']}")
        
        # Warn about weak patterns
        if weak_patterns and not valid_patterns:
            insights.append(f"⚠️ {len(weak_patterns)} pattern(s) detected but trend context is wrong - signals are WEAK")

        if not patterns:
            insights.append("No significant candlestick patterns detected in the lookback period")

        result["insights"] = insights
        
        # Overall signal based on valid patterns only
        if len(bullish_valid) > len(bearish_valid) and bullish_valid:
            result["overall_signal"] = "bullish"
        elif len(bearish_valid) > len(bullish_valid) and bearish_valid:
            result["overall_signal"] = "bearish"
        else:
            result["overall_signal"] = "neutral"

        return result

    except Exception as e:
        return {
            "ticker": ticker,
            "error": str(e),
        }
