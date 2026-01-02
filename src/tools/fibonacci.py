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


def find_pivot_highs(df: pd.DataFrame, left_bars: int = 3, right_bars: int = 3) -> List[Tuple[int, float]]:
    """
    Find confirmed pivot highs using N-bar confirmation.
    
    A pivot high requires:
    - The high is HIGHER than all bars within left_bars before it
    - The high is HIGHER than all bars within right_bars after it
    
    This eliminates noise/spikes and finds true swing points.
    
    Args:
        df: DataFrame with OHLCV data
        left_bars: Number of bars to check on the left
        right_bars: Number of bars to check on the right
        
    Returns:
        List of tuples (index, price) for each pivot high
    """
    pivot_highs = []
    high_prices = df['High'].values
    
    for i in range(left_bars, len(high_prices) - right_bars):
        is_pivot = True
        
        # Check left side
        for j in range(1, left_bars + 1):
            if high_prices[i] <= high_prices[i - j]:
                is_pivot = False
                break
        
        # Check right side (only if left passed)
        if is_pivot:
            for j in range(1, right_bars + 1):
                if high_prices[i] <= high_prices[i + j]:
                    is_pivot = False
                    break
        
        if is_pivot:
            pivot_highs.append((i, float(high_prices[i])))
    
    return pivot_highs


def find_pivot_lows(df: pd.DataFrame, left_bars: int = 3, right_bars: int = 3) -> List[Tuple[int, float]]:
    """
    Find confirmed pivot lows using N-bar confirmation.
    
    A pivot low requires:
    - The low is LOWER than all bars within left_bars before it
    - The low is LOWER than all bars within right_bars after it
    
    Args:
        df: DataFrame with OHLCV data
        left_bars: Number of bars to check on the left
        right_bars: Number of bars to check on the right
        
    Returns:
        List of tuples (index, price) for each pivot low
    """
    pivot_lows = []
    low_prices = df['Low'].values
    
    for i in range(left_bars, len(low_prices) - right_bars):
        is_pivot = True
        
        # Check left side
        for j in range(1, left_bars + 1):
            if low_prices[i] >= low_prices[i - j]:
                is_pivot = False
                break
        
        # Check right side (only if left passed)
        if is_pivot:
            for j in range(1, right_bars + 1):
                if low_prices[i] >= low_prices[i + j]:
                    is_pivot = False
                    break
        
        if is_pivot:
            pivot_lows.append((i, float(low_prices[i])))
    
    return pivot_lows


def detect_swing_points(df: pd.DataFrame, window: int = 5) -> Tuple[float, float, int, int, Dict[str, Any]]:
    """
    Detect swing high and swing low points using proper pivot detection.
    
    Uses N-bar confirmation algorithm:
    1. Find all confirmed pivot highs (bars higher than N bars on each side)
    2. Find all confirmed pivot lows (bars lower than N bars on each side)
    3. Select the most significant ones for Fibonacci calculation
    4. Fallback to simple max/min if no pivots found

    Args:
        df: DataFrame with OHLCV data
        window: Window size for detecting swing points (used as left/right bars)

    Returns:
        Tuple of (swing_high, swing_low, high_index, low_index, detection_info)
    """
    high_prices = df['High'].values
    low_prices = df['Low'].values
    
    # Use adaptive window based on data length
    # For shorter periods, use smaller window
    data_len = len(high_prices)
    if data_len < 30:
        left_bars = right_bars = 2
    elif data_len < 60:
        left_bars = right_bars = 3
    else:
        left_bars = right_bars = min(window, 5)
    
    detection_method = "pivot"
    pivot_high_count = 0
    pivot_low_count = 0
    
    # Find pivot highs
    pivot_highs = find_pivot_highs(df, left_bars, right_bars)
    pivot_high_count = len(pivot_highs)
    
    if pivot_highs:
        # Select the highest pivot high
        swing_high_idx, swing_high = max(pivot_highs, key=lambda x: x[1])
    else:
        # Fallback to simple max if no pivots found
        swing_high_idx = int(np.argmax(high_prices))
        swing_high = float(high_prices[swing_high_idx])
        detection_method = "fallback_max"
    
    # Find pivot lows
    pivot_lows = find_pivot_lows(df, left_bars, right_bars)
    pivot_low_count = len(pivot_lows)
    
    if pivot_lows:
        # Select the lowest pivot low
        swing_low_idx, swing_low = min(pivot_lows, key=lambda x: x[1])
    else:
        # Fallback to simple min if no pivots found
        swing_low_idx = int(np.argmin(low_prices))
        swing_low = float(low_prices[swing_low_idx])
        if detection_method == "pivot":
            detection_method = "fallback_min"
        else:
            detection_method = "fallback_both"
    
    # Prepare detection info for transparency
    detection_info = {
        "method": detection_method,
        "left_bars": left_bars,
        "right_bars": right_bars,
        "pivot_highs_found": pivot_high_count,
        "pivot_lows_found": pivot_low_count,
        "swing_high_date": str(df.index[swing_high_idx].date()) if hasattr(df.index[swing_high_idx], 'date') else str(df.index[swing_high_idx]),
        "swing_low_date": str(df.index[swing_low_idx].date()) if hasattr(df.index[swing_low_idx], 'date') else str(df.index[swing_low_idx]),
    }

    return swing_high, swing_low, swing_high_idx, swing_low_idx, detection_info


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
    
    Extension = proyeksi target harga BEYOND swing high/low
    Formula yang benar:
    - Uptrend: swing_low + (range × ratio) → target di atas swing_high
    - Downtrend: swing_high - (range × ratio) → target di bawah swing_low

    Args:
        swing_high: Swing high price
        swing_low: Swing low price
        is_uptrend: True if uptrend, False if downtrend

    Returns:
        Dictionary of Fibonacci extension levels
    """
    diff = swing_high - swing_low

    # Extension ratios (beyond 100%)
    ext_ratios = {
        "127.2%": 1.272,
        "161.8%": 1.618,
        "200.0%": 2.000,
        "261.8%": 2.618,  # Added for IDX yang sering ARA beruntun
    }

    levels = {}

    if is_uptrend:
        # For uptrend: extensions proyeksi dari swing_low ke atas
        # Target = swing_low + (range × ratio)
        for label, ratio in ext_ratios.items():
            levels[label] = round(swing_low + (diff * ratio), 2)
    else:
        # For downtrend: extensions proyeksi dari swing_high ke bawah
        # Target = swing_high - (range × ratio)
        for label, ratio in ext_ratios.items():
            levels[label] = round(swing_high - (diff * ratio), 2)

    return levels


def determine_trend(df: pd.DataFrame) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Determine if the trend is uptrend or downtrend using multiple methods.
    
    Methods used:
    1. MA Slope: SMA20 slope over recent bars (most reliable)
    2. Higher-Highs/Lower-Lows pattern (classic trend definition)
    3. Price position vs MA
    
    This is more robust than simple half-average comparison which can be
    fooled by sideways markets with a single spike.

    Args:
        df: DataFrame with OHLCV data

    Returns:
        Tuple of (is_uptrend, confidence, trend_info_dict)
    """
    closes = df['Close'].values
    highs = df['High'].values
    lows = df['Low'].values
    
    trend_info = {
        "ma_slope_pct": 0.0,
        "higher_highs": False,
        "higher_lows": False,
        "lower_highs": False,
        "lower_lows": False,
        "price_vs_ma": "unknown",
    }
    
    bullish_signals = 0
    bearish_signals = 0
    
    # Method 1: MA Slope (SMA20)
    if len(closes) >= 20:
        sma20 = pd.Series(closes).rolling(20, min_periods=10).mean()
        # Calculate slope of last 10 days of MA
        recent_ma = sma20.iloc[-10:].dropna()
        if len(recent_ma) >= 2 and recent_ma.iloc[0] > 0:
            ma_slope = (recent_ma.iloc[-1] - recent_ma.iloc[0]) / recent_ma.iloc[0] * 100
            trend_info["ma_slope_pct"] = round(ma_slope, 2)
            
            if ma_slope > 2:  # MA slope > 2%
                bullish_signals += 2
            elif ma_slope > 0.5:
                bullish_signals += 1
            elif ma_slope < -2:
                bearish_signals += 2
            elif ma_slope < -0.5:
                bearish_signals += 1
        
        # Price vs MA position
        current_price = closes[-1]
        current_ma = sma20.iloc[-1]
        if pd.notna(current_ma) and current_ma > 0:
            if current_price > current_ma:
                trend_info["price_vs_ma"] = "above"
                bullish_signals += 1
            else:
                trend_info["price_vs_ma"] = "below"
                bearish_signals += 1
    
    # Method 2: Higher-Highs/Lower-Lows pattern (check recent 20 bars or all if less)
    check_bars = min(20, len(highs) - 1)
    if check_bars >= 10:
        mid = check_bars // 2
        recent_highs = highs[-check_bars:]
        recent_lows = lows[-check_bars:]
        
        # First half vs second half comparison for HH/HL/LH/LL
        first_half_high = np.max(recent_highs[:mid])
        second_half_high = np.max(recent_highs[mid:])
        first_half_low = np.min(recent_lows[:mid])
        second_half_low = np.min(recent_lows[mid:])
        
        # Higher Highs: second half made new high above first half
        higher_highs = second_half_high > first_half_high
        trend_info["higher_highs"] = bool(higher_highs)
        
        # Higher Lows: second half low is above first half low
        higher_lows = second_half_low > first_half_low
        trend_info["higher_lows"] = bool(higher_lows)
        
        # Lower Highs: second half high is below first half high
        lower_highs = second_half_high < first_half_high
        trend_info["lower_highs"] = bool(lower_highs)
        
        # Lower Lows: second half made new low below first half
        lower_lows = second_half_low < first_half_low
        trend_info["lower_lows"] = bool(lower_lows)
        
        # Classic uptrend: Higher Highs AND Higher Lows
        if higher_highs and higher_lows:
            bullish_signals += 3  # Strong signal
        elif higher_highs:
            bullish_signals += 1
        elif higher_lows:
            bullish_signals += 1
        
        # Classic downtrend: Lower Highs AND Lower Lows
        if lower_highs and lower_lows:
            bearish_signals += 3  # Strong signal
        elif lower_lows:
            bearish_signals += 1
        elif lower_highs:
            bearish_signals += 1
    
    # Determine final trend
    if bullish_signals > bearish_signals:
        is_uptrend = True
        if bullish_signals >= 5:
            confidence = "high"
        elif bullish_signals >= 3:
            confidence = "medium"
        else:
            confidence = "low"
    elif bearish_signals > bullish_signals:
        is_uptrend = False
        if bearish_signals >= 5:
            confidence = "high"
        elif bearish_signals >= 3:
            confidence = "medium"
        else:
            confidence = "low"
    else:
        # Tie or sideways - use simple price comparison as tiebreaker
        is_uptrend = closes[-1] > closes[0]
        confidence = "low"
    
    trend_info["bullish_signals"] = bullish_signals
    trend_info["bearish_signals"] = bearish_signals

    return is_uptrend, confidence, trend_info


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

        # Detect swing points using proper pivot detection
        swing_high, swing_low, high_idx, low_idx, detection_info = detect_swing_points(df)

        # Determine trend using multiple methods
        if trend_param == "auto":
            is_uptrend, trend_confidence, trend_info = determine_trend(df)
            trend_direction = "uptrend" if is_uptrend else "downtrend"
        else:
            is_uptrend = trend_param == "uptrend"
            trend_direction = trend_param
            trend_confidence = "user_specified"
            trend_info = {"user_override": True}

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
        
        # Calculate price position as percentage within the range
        price_range = swing_high - swing_low
        if price_range > 0:
            range_position_pct = round((current_price - swing_low) / price_range * 100, 1)
        else:
            range_position_pct = 50.0

        result = {
            "ticker": ticker,
            "period": period,
            "current_price": current_price,
            "trend": {
                "direction": trend_direction,
                "confidence": trend_confidence,
                "analysis": trend_info,
            },
            "swing_points": {
                "high": round(swing_high, 2),
                "low": round(swing_low, 2),
                "range": round(price_range, 2),
                "range_pct": round(price_range / swing_low * 100, 2) if swing_low > 0 else 0,
                "detection": detection_info,
            },
            "price_position": {
                "description": position_description,
                "range_position_pct": range_position_pct,  # 0% = at low, 100% = at high
            },
            "retracement_levels": retracement_levels,
            "extension_levels": extension_levels,
            "nearest_support": {
                "level": support_label,
                "price": support_level,
                "distance_pct": round((current_price - support_level) / current_price * 100, 2) if support_level > 0 else None,
            },
            "nearest_resistance": {
                "level": resistance_label,
                "price": resistance_level,
                "distance_pct": round((resistance_level - current_price) / current_price * 100, 2) if resistance_level > 0 else None,
            },
            "risk_reward_ratio": risk_reward_ratio,
            "insights": _generate_fib_insights(
                current_price, swing_high, swing_low, trend_direction,
                support_label, resistance_label, risk_reward_ratio, range_position_pct
            ),
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


def _generate_fib_insights(
    current_price: float,
    swing_high: float,
    swing_low: float,
    trend: str,
    support_label: str,
    resistance_label: str,
    rr_ratio: float,
    range_position: float
) -> List[str]:
    """Generate trading insights based on Fibonacci analysis."""
    insights = []
    
    # Trend insight
    if trend == "uptrend":
        insights.append("📈 Trend: UPTREND - Fibonacci retracement levels sebagai support")
    else:
        insights.append("📉 Trend: DOWNTREND - Fibonacci retracement levels sebagai resistance")
    
    # Position insight
    if range_position >= 80:
        insights.append("⚠️ Harga dekat swing high - hati-hati resistance")
    elif range_position <= 20:
        insights.append("👀 Harga dekat swing low - perhatikan support")
    elif 45 <= range_position <= 55:
        insights.append("🎯 Harga di tengah range - watch for breakout direction")
    
    # Key levels
    if support_label != "N/A":
        insights.append(f"🛡️ Support terdekat: {support_label}")
    if resistance_label != "N/A":
        insights.append(f"🎯 Resistance terdekat: {resistance_label}")
    
    # Risk/Reward
    if rr_ratio >= 2:
        insights.append(f"✅ Risk/Reward ratio bagus: {rr_ratio}:1")
    elif rr_ratio >= 1:
        insights.append(f"🟡 Risk/Reward ratio moderate: {rr_ratio}:1")
    elif rr_ratio > 0:
        insights.append(f"⚠️ Risk/Reward ratio kurang ideal: {rr_ratio}:1")
    
    # Key Fibonacci levels insight
    insights.append("💡 Level penting: 38.2%, 50%, 61.8% (golden ratio)")
    
    return insights
