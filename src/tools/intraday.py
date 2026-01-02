"""Tools for intraday trading analysis - VWAP, Pivot Points, Gap Analysis."""

from typing import Any, Dict, List, Tuple
import pandas as pd
import numpy as np
from mcp.types import Tool
from src.utils.yahoo import yahoo_client, YahooFinanceError
from src.utils.validators import validate_ticker
from src.utils.exceptions import InvalidParameterError, DataUnavailableError, NetworkError
from src.utils.cache import cache_manager


# ============================================================================
# VWAP (Volume Weighted Average Price)
# ============================================================================

def get_vwap_tool() -> Tool:
    """Get VWAP tool definition."""
    return Tool(
        name="get_vwap",
        description="Menghitung VWAP (Volume Weighted Average Price) untuk intraday trading. VWAP adalah benchmark institusional untuk fair value intraday.",
        inputSchema={
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Ticker saham IDX (contoh: BBCA, BBRI, TLKM)",
                },
                "period": {
                    "type": "string",
                    "description": "Periode data (1d untuk intraday, 5d untuk multi-day VWAP)",
                    "default": "5d",
                    "enum": ["1d", "5d", "1mo"],
                },
                "include_bands": {
                    "type": "boolean",
                    "description": "Include VWAP bands (1 & 2 standard deviation)",
                    "default": True,
                },
            },
            "required": ["ticker"],
        },
    )


def calculate_vwap(df: pd.DataFrame) -> Tuple[float, pd.Series]:
    """
    Calculate VWAP from OHLCV data.
    
    VWAP = Cumulative(Typical Price × Volume) / Cumulative(Volume)
    Typical Price = (High + Low + Close) / 3
    
    Args:
        df: DataFrame with High, Low, Close, Volume columns
        
    Returns:
        Tuple of (current_vwap, vwap_series)
    """
    # Calculate typical price
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    
    # Calculate VWAP
    tp_volume = typical_price * df['Volume']
    cumulative_tp_volume = tp_volume.cumsum()
    cumulative_volume = df['Volume'].cumsum()
    
    vwap_series = cumulative_tp_volume / cumulative_volume
    current_vwap = vwap_series.iloc[-1] if not vwap_series.empty else 0
    
    return float(current_vwap), vwap_series


def calculate_vwap_bands(df: pd.DataFrame, vwap_series: pd.Series, num_std: int = 2) -> Dict[str, float]:
    """
    Calculate VWAP standard deviation bands.
    
    Args:
        df: DataFrame with OHLCV data
        vwap_series: VWAP series
        num_std: Number of standard deviations for bands
        
    Returns:
        Dictionary with band levels
    """
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    
    # Calculate squared deviation from VWAP
    squared_deviation = (typical_price - vwap_series) ** 2
    
    # Volume-weighted standard deviation
    vw_variance = (squared_deviation * df['Volume']).cumsum() / df['Volume'].cumsum()
    vw_std = np.sqrt(vw_variance)
    
    current_vwap = vwap_series.iloc[-1]
    current_std = vw_std.iloc[-1] if not vw_std.empty else 0
    
    bands = {}
    for i in range(1, num_std + 1):
        bands[f"upper_{i}std"] = round(current_vwap + (current_std * i), 2)
        bands[f"lower_{i}std"] = round(current_vwap - (current_std * i), 2)
    
    bands["std_value"] = round(current_std, 2)
    
    return bands


def interpret_vwap_position(current_price: float, vwap: float, bands: Dict[str, float]) -> Dict[str, Any]:
    """
    Interpret price position relative to VWAP.
    
    Args:
        current_price: Current stock price
        vwap: Current VWAP value
        bands: VWAP bands dictionary
        
    Returns:
        Dictionary with interpretation
    """
    deviation_pct = ((current_price - vwap) / vwap * 100) if vwap > 0 else 0
    
    # Determine position
    if current_price > bands.get("upper_2std", vwap * 1.1):
        position = "far_above_vwap"
        signal = "🔴 OVERBOUGHT - Price sangat jauh di atas VWAP"
    elif current_price > bands.get("upper_1std", vwap * 1.05):
        position = "above_upper_band"
        signal = "🟡 CAUTION - Price di atas upper band"
    elif current_price > vwap:
        position = "above_vwap"
        signal = "🟢 BULLISH - Buyers in control (di atas VWAP)"
    elif current_price > bands.get("lower_1std", vwap * 0.95):
        position = "below_vwap"
        signal = "🔴 BEARISH - Sellers in control (di bawah VWAP)"
    elif current_price > bands.get("lower_2std", vwap * 0.9):
        position = "below_lower_band"
        signal = "🟡 OVERSOLD - Price di bawah lower band"
    else:
        position = "far_below_vwap"
        signal = "🔴 EXTREME OVERSOLD - Price sangat jauh di bawah VWAP"
    
    return {
        "position": position,
        "deviation_pct": round(deviation_pct, 2),
        "signal": signal,
        "interpretation": "bullish" if current_price > vwap else "bearish",
    }


async def get_vwap(args: dict[str, Any]) -> dict[str, Any]:
    """
    Calculate VWAP with bands and interpretation.
    
    Args:
        args: Dictionary with 'ticker', optional 'period' and 'include_bands'
        
    Returns:
        Dictionary with VWAP analysis
    """
    try:
        ticker = validate_ticker(args.get("ticker", ""))
        period = args.get("period", "5d")
        include_bands = args.get("include_bands", True)
        
        # Validate period
        valid_periods = ["1d", "5d", "1mo"]
        if period not in valid_periods:
            period = "5d"
        
        # Determine interval based on period
        # For intraday VWAP, use smaller intervals when available
        interval = "15m" if period in ["1d", "5d"] else "1h"
        
        # Check cache
        cache_key = cache_manager.generate_key("vwap", ticker, period)
        cached = cache_manager.get("realtime", cache_key)
        if cached:
            return cached
        
        # Get historical data
        hist_data = yahoo_client.get_historical_data(ticker, period=period, interval=interval)
        if "error" in hist_data:
            # Fallback to daily data if intraday not available
            hist_data = yahoo_client.get_historical_data(ticker, period="1mo", interval="1d")
            if "error" in hist_data:
                raise DataUnavailableError(f"Tidak dapat mengambil data untuk {ticker}")
        
        if not hist_data.get("data") or len(hist_data["data"]) < 2:
            raise DataUnavailableError(f"Data tidak cukup untuk menghitung VWAP {ticker}")
        
        # Convert to DataFrame
        df = pd.DataFrame(hist_data["data"])
        df["Date"] = pd.to_datetime(df["date"])
        df.set_index("Date", inplace=True)
        df.sort_index(inplace=True)
        
        # Rename columns
        df.rename(columns={
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume"
        }, inplace=True)
        
        # Ensure numeric
        for col in ["Open", "High", "Low", "Close", "Volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        
        df = df.dropna()
        
        if df.empty or len(df) < 2:
            raise DataUnavailableError(f"Data tidak valid untuk VWAP {ticker}")
        
        # Get current price
        price_data = yahoo_client.get_current_price(ticker)
        current_price = price_data.get("price", df['Close'].iloc[-1])
        
        # Calculate VWAP
        vwap_value, vwap_series = calculate_vwap(df)
        
        # Calculate bands if requested
        bands = {}
        if include_bands:
            bands = calculate_vwap_bands(df, vwap_series, num_std=2)
        
        # Interpret position
        interpretation = interpret_vwap_position(current_price, vwap_value, bands)
        
        # Calculate daily VWAP for today (if multi-day data)
        today_vwap = None
        if len(df) > 1:
            # Try to get today's data only
            today = df.index[-1].date() if hasattr(df.index[-1], 'date') else None
            if today:
                today_df = df[df.index.date == today] if hasattr(df.index, 'date') else df.tail(1)
                if len(today_df) > 0:
                    today_vwap_val, _ = calculate_vwap(today_df)
                    today_vwap = round(today_vwap_val, 2)
        
        # Trading guidance
        if interpretation["position"] in ["above_vwap"]:
            trading_bias = "LONG - Buy dips ke VWAP"
            entry_zone = f"Rp {round(vwap_value, 0):,.0f} - Rp {round(bands.get('upper_1std', vwap_value * 1.02), 0):,.0f}"
        elif interpretation["position"] in ["below_vwap"]:
            trading_bias = "SHORT/AVOID - Wait for reclaim VWAP"
            entry_zone = f"Reclaim di atas Rp {round(vwap_value, 0):,.0f}"
        elif interpretation["position"] in ["far_above_vwap", "above_upper_band"]:
            trading_bias = "CAUTION - Extended, wait for pullback"
            entry_zone = f"Pullback ke Rp {round(bands.get('upper_1std', vwap_value), 0):,.0f}"
        else:
            trading_bias = "OVERSOLD - Watch for bounce"
            entry_zone = f"Bounce dari Rp {round(bands.get('lower_1std', vwap_value), 0):,.0f}"
        
        result = {
            "ticker": ticker,
            "name": price_data.get("name", ""),
            "current_price": round(current_price, 2),
            "vwap": round(vwap_value, 2),
            "today_vwap": today_vwap,
            "deviation_from_vwap": round(current_price - vwap_value, 2),
            "deviation_percent": interpretation["deviation_pct"],
            "position": interpretation["position"],
            "signal": interpretation["signal"],
            "interpretation": interpretation["interpretation"],
            "bands": bands if include_bands else None,
            "trading_guidance": {
                "bias": trading_bias,
                "entry_zone": entry_zone,
                "stop_reference": f"VWAP @ Rp {round(vwap_value, 0):,.0f}",
            },
            "data_info": {
                "period": period,
                "interval": interval,
                "data_points": len(df),
            },
            "insights": [
                interpretation["signal"],
                f"VWAP: Rp {round(vwap_value, 0):,.0f}" + (f" | Today VWAP: Rp {today_vwap:,.0f}" if today_vwap else ""),
                f"Deviation: {interpretation['deviation_pct']:+.2f}%",
            ],
        }
        
        # Cache result (short TTL for intraday)
        cache_manager.set("realtime", cache_key, result)
        
        return result
        
    except ValueError as e:
        raise InvalidParameterError(str(e))
    except YahooFinanceError as e:
        raise DataUnavailableError(str(e))
    except (InvalidParameterError, DataUnavailableError):
        raise
    except Exception as e:
        raise NetworkError(f"Gagal menghitung VWAP: {str(e)}")


# ============================================================================
# PIVOT POINTS
# ============================================================================

def get_pivot_points_tool() -> Tool:
    """Get Pivot Points tool definition."""
    return Tool(
        name="get_pivot_points",
        description="Menghitung Pivot Points untuk support/resistance intraday. Termasuk Standard, Fibonacci, Woodie, dan Camarilla pivots.",
        inputSchema={
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Ticker saham IDX (contoh: BBCA, BBRI, TLKM)",
                },
                "pivot_type": {
                    "type": "string",
                    "description": "Tipe pivot calculation",
                    "enum": ["standard", "fibonacci", "woodie", "camarilla", "all"],
                    "default": "standard",
                },
            },
            "required": ["ticker"],
        },
    )


def calculate_standard_pivots(high: float, low: float, close: float) -> Dict[str, float]:
    """
    Calculate Standard (Classic) Pivot Points.
    
    PP = (H + L + C) / 3
    R1 = 2×PP - L
    R2 = PP + (H - L)
    R3 = H + 2×(PP - L)
    S1 = 2×PP - H
    S2 = PP - (H - L)
    S3 = L - 2×(H - PP)
    """
    pp = (high + low + close) / 3
    
    return {
        "PP": round(pp, 2),
        "R1": round(2 * pp - low, 2),
        "R2": round(pp + (high - low), 2),
        "R3": round(high + 2 * (pp - low), 2),
        "S1": round(2 * pp - high, 2),
        "S2": round(pp - (high - low), 2),
        "S3": round(low - 2 * (high - pp), 2),
    }


def calculate_fibonacci_pivots(high: float, low: float, close: float) -> Dict[str, float]:
    """
    Calculate Fibonacci Pivot Points.
    
    PP = (H + L + C) / 3
    R1 = PP + 0.382×(H - L)
    R2 = PP + 0.618×(H - L)
    R3 = PP + 1.000×(H - L)
    S1 = PP - 0.382×(H - L)
    S2 = PP - 0.618×(H - L)
    S3 = PP - 1.000×(H - L)
    """
    pp = (high + low + close) / 3
    range_hl = high - low
    
    return {
        "PP": round(pp, 2),
        "R1": round(pp + 0.382 * range_hl, 2),
        "R2": round(pp + 0.618 * range_hl, 2),
        "R3": round(pp + 1.000 * range_hl, 2),
        "S1": round(pp - 0.382 * range_hl, 2),
        "S2": round(pp - 0.618 * range_hl, 2),
        "S3": round(pp - 1.000 * range_hl, 2),
    }


def calculate_woodie_pivots(high: float, low: float, close: float, open_price: float) -> Dict[str, float]:
    """
    Calculate Woodie Pivot Points.
    Gives more weight to close price.
    
    PP = (H + L + 2×C) / 4
    R1 = 2×PP - L
    R2 = PP + (H - L)
    S1 = 2×PP - H
    S2 = PP - (H - L)
    """
    pp = (high + low + 2 * close) / 4
    
    return {
        "PP": round(pp, 2),
        "R1": round(2 * pp - low, 2),
        "R2": round(pp + (high - low), 2),
        "S1": round(2 * pp - high, 2),
        "S2": round(pp - (high - low), 2),
    }


def calculate_camarilla_pivots(high: float, low: float, close: float) -> Dict[str, float]:
    """
    Calculate Camarilla Pivot Points.
    Better for intraday trading with tighter levels.
    
    R4 = C + (H - L) × 1.1/2
    R3 = C + (H - L) × 1.1/4
    R2 = C + (H - L) × 1.1/6
    R1 = C + (H - L) × 1.1/12
    S1 = C - (H - L) × 1.1/12
    S2 = C - (H - L) × 1.1/6
    S3 = C - (H - L) × 1.1/4
    S4 = C - (H - L) × 1.1/2
    """
    range_hl = high - low
    
    return {
        "R4": round(close + range_hl * 1.1 / 2, 2),
        "R3": round(close + range_hl * 1.1 / 4, 2),
        "R2": round(close + range_hl * 1.1 / 6, 2),
        "R1": round(close + range_hl * 1.1 / 12, 2),
        "PP": round((high + low + close) / 3, 2),  # Standard PP for reference
        "S1": round(close - range_hl * 1.1 / 12, 2),
        "S2": round(close - range_hl * 1.1 / 6, 2),
        "S3": round(close - range_hl * 1.1 / 4, 2),
        "S4": round(close - range_hl * 1.1 / 2, 2),
    }


def find_nearest_pivot_levels(current_price: float, pivots: Dict[str, float]) -> Dict[str, Any]:
    """
    Find nearest support and resistance from pivot levels.
    
    Args:
        current_price: Current stock price
        pivots: Dictionary of pivot levels
        
    Returns:
        Dictionary with nearest levels
    """
    # Sort levels by price
    sorted_levels = sorted(pivots.items(), key=lambda x: x[1])
    
    nearest_support = None
    nearest_resistance = None
    
    for level_name, level_price in sorted_levels:
        if level_price < current_price:
            nearest_support = {"level": level_name, "price": level_price}
        elif level_price > current_price and nearest_resistance is None:
            nearest_resistance = {"level": level_name, "price": level_price}
    
    # Calculate distances
    support_distance = None
    resistance_distance = None
    
    if nearest_support:
        support_distance = {
            "points": round(current_price - nearest_support["price"], 2),
            "percent": round((current_price - nearest_support["price"]) / current_price * 100, 2),
        }
    
    if nearest_resistance:
        resistance_distance = {
            "points": round(nearest_resistance["price"] - current_price, 2),
            "percent": round((nearest_resistance["price"] - current_price) / current_price * 100, 2),
        }
    
    return {
        "nearest_support": nearest_support,
        "nearest_resistance": nearest_resistance,
        "support_distance": support_distance,
        "resistance_distance": resistance_distance,
    }


def determine_pivot_position(current_price: float, pivots: Dict[str, float]) -> str:
    """Determine position relative to pivot point."""
    pp = pivots.get("PP", 0)
    
    if pp == 0:
        return "unknown"
    
    # Check against major levels
    r3 = pivots.get("R3", pivots.get("R4", pp * 1.1))
    r2 = pivots.get("R2", pp * 1.05)
    r1 = pivots.get("R1", pp * 1.02)
    s1 = pivots.get("S1", pp * 0.98)
    s2 = pivots.get("S2", pp * 0.95)
    s3 = pivots.get("S3", pivots.get("S4", pp * 0.9))
    
    if current_price >= r3:
        return "above_R3"
    elif current_price >= r2:
        return "between_R2_R3"
    elif current_price >= r1:
        return "between_R1_R2"
    elif current_price >= pp:
        return "between_PP_R1"
    elif current_price >= s1:
        return "between_S1_PP"
    elif current_price >= s2:
        return "between_S2_S1"
    elif current_price >= s3:
        return "between_S3_S2"
    else:
        return "below_S3"


async def get_pivot_points(args: dict[str, Any]) -> dict[str, Any]:
    """
    Calculate Pivot Points for intraday trading.
    
    Args:
        args: Dictionary with 'ticker' and optional 'pivot_type'
        
    Returns:
        Dictionary with pivot points analysis
    """
    try:
        ticker = validate_ticker(args.get("ticker", ""))
        pivot_type = args.get("pivot_type", "standard")
        
        # Validate pivot_type
        valid_types = ["standard", "fibonacci", "woodie", "camarilla", "all"]
        if pivot_type not in valid_types:
            pivot_type = "standard"
        
        # Check cache
        cache_key = cache_manager.generate_key("pivot_points", ticker, pivot_type)
        cached = cache_manager.get("realtime", cache_key)
        if cached:
            return cached
        
        # Get yesterday's OHLC data for pivot calculation
        # Pivot points use PREVIOUS day's data to calculate TODAY's levels
        hist_data = yahoo_client.get_historical_data(ticker, period="5d", interval="1d")
        if "error" in hist_data:
            raise DataUnavailableError(f"Tidak dapat mengambil data untuk {ticker}")
        
        if not hist_data.get("data") or len(hist_data["data"]) < 2:
            raise DataUnavailableError(f"Data tidak cukup untuk menghitung Pivot Points {ticker}")
        
        # Get previous day's OHLC (second to last entry is yesterday)
        df = pd.DataFrame(hist_data["data"])
        df = df.sort_values("date")  # Ensure sorted by date
        
        # Yesterday's data for pivot calculation
        yesterday = df.iloc[-2]
        prev_high = float(yesterday["high"])
        prev_low = float(yesterday["low"])
        prev_close = float(yesterday["close"])
        prev_open = float(yesterday["open"])
        
        # Today's data
        today = df.iloc[-1]
        today_open = float(today["open"])
        today_high = float(today["high"])
        today_low = float(today["low"])
        
        # Get current price
        price_data = yahoo_client.get_current_price(ticker)
        current_price = price_data.get("price", float(today["close"]))
        
        # Calculate pivots based on type
        pivots = {}
        primary_pivots = {}
        
        if pivot_type == "standard" or pivot_type == "all":
            standard = calculate_standard_pivots(prev_high, prev_low, prev_close)
            pivots["standard"] = standard
            if pivot_type == "standard":
                primary_pivots = standard
        
        if pivot_type == "fibonacci" or pivot_type == "all":
            fibonacci = calculate_fibonacci_pivots(prev_high, prev_low, prev_close)
            pivots["fibonacci"] = fibonacci
            if pivot_type == "fibonacci":
                primary_pivots = fibonacci
        
        if pivot_type == "woodie" or pivot_type == "all":
            woodie = calculate_woodie_pivots(prev_high, prev_low, prev_close, prev_open)
            pivots["woodie"] = woodie
            if pivot_type == "woodie":
                primary_pivots = woodie
        
        if pivot_type == "camarilla" or pivot_type == "all":
            camarilla = calculate_camarilla_pivots(prev_high, prev_low, prev_close)
            pivots["camarilla"] = camarilla
            if pivot_type == "camarilla":
                primary_pivots = camarilla
        
        if pivot_type == "all":
            primary_pivots = pivots["standard"]  # Use standard as primary
        
        # Find nearest levels
        nearest = find_nearest_pivot_levels(current_price, primary_pivots)
        
        # Determine position
        position = determine_pivot_position(current_price, primary_pivots)
        
        # Generate signal
        pp = primary_pivots.get("PP", 0)
        if current_price > pp:
            bias = "BULLISH"
            signal = "🟢 Price di atas Pivot Point - Bullish bias"
        else:
            bias = "BEARISH"
            signal = "🔴 Price di bawah Pivot Point - Bearish bias"
        
        # Trading guidance based on position
        if "above_R" in position or position == "between_R2_R3":
            guidance = "EXTENDED - Consider taking profits or wait for pullback"
            risk_level = "HIGH"
        elif position in ["between_PP_R1", "between_R1_R2"]:
            guidance = "BULLISH - Buy dips to PP/R1, target R2/R3"
            risk_level = "MODERATE"
        elif position == "between_S1_PP":
            guidance = "NEUTRAL - Watch for break above PP or below S1"
            risk_level = "MODERATE"
        elif position in ["between_S2_S1", "between_S3_S2"]:
            guidance = "OVERSOLD - Watch for bounce, buy near S2/S3"
            risk_level = "MODERATE"
        else:
            guidance = "EXTREME OVERSOLD - High risk zone"
            risk_level = "HIGH"
        
        # Today's range analysis
        today_range = today_high - today_low
        yesterday_range = prev_high - prev_low
        range_expansion = today_range > yesterday_range
        
        result = {
            "ticker": ticker,
            "name": price_data.get("name", ""),
            "current_price": round(current_price, 2),
            "pivot_type": pivot_type,
            "pivots": pivots if pivot_type == "all" else {pivot_type: primary_pivots},
            "primary_levels": primary_pivots,
            "position": position,
            "bias": bias,
            "signal": signal,
            "nearest_support": nearest["nearest_support"],
            "nearest_resistance": nearest["nearest_resistance"],
            "support_distance": nearest["support_distance"],
            "resistance_distance": nearest["resistance_distance"],
            "trading_guidance": {
                "guidance": guidance,
                "risk_level": risk_level,
                "long_entry": nearest["nearest_support"]["price"] if nearest["nearest_support"] else None,
                "long_target": nearest["nearest_resistance"]["price"] if nearest["nearest_resistance"] else None,
                "stop_loss": primary_pivots.get("S2", primary_pivots.get("S3")),
            },
            "yesterday_ohlc": {
                "open": prev_open,
                "high": prev_high,
                "low": prev_low,
                "close": prev_close,
            },
            "today_range": {
                "open": today_open,
                "high": today_high,
                "low": today_low,
                "current": current_price,
                "range": round(today_range, 2),
                "range_vs_yesterday": "expanding" if range_expansion else "contracting",
            },
            "insights": [
                signal,
                f"PP: Rp {primary_pivots.get('PP', 0):,.0f}",
                f"Nearest Support: {nearest['nearest_support']['level']} @ Rp {nearest['nearest_support']['price']:,.0f}" if nearest["nearest_support"] else "No support below",
                f"Nearest Resistance: {nearest['nearest_resistance']['level']} @ Rp {nearest['nearest_resistance']['price']:,.0f}" if nearest["nearest_resistance"] else "No resistance above",
            ],
        }
        
        # Cache result
        cache_manager.set("realtime", cache_key, result)
        
        return result
        
    except ValueError as e:
        raise InvalidParameterError(str(e))
    except YahooFinanceError as e:
        raise DataUnavailableError(str(e))
    except (InvalidParameterError, DataUnavailableError):
        raise
    except Exception as e:
        raise NetworkError(f"Gagal menghitung Pivot Points: {str(e)}")


# ============================================================================
# GAP ANALYSIS
# ============================================================================

def get_gap_analysis_tool() -> Tool:
    """Get Gap Analysis tool definition."""
    return Tool(
        name="get_gap_analysis",
        description="Menganalisis gap (celah harga) dari previous close ke today's open. Berguna untuk intraday trading dan gap fill strategies.",
        inputSchema={
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Ticker saham IDX (contoh: BBCA, BBRI, TLKM)",
                },
            },
            "required": ["ticker"],
        },
    )


async def get_gap_analysis(args: dict[str, Any]) -> dict[str, Any]:
    """
    Analyze gap between previous close and today's open.
    
    Args:
        args: Dictionary with 'ticker'
        
    Returns:
        Dictionary with gap analysis
    """
    try:
        ticker = validate_ticker(args.get("ticker", ""))
        
        # Check cache
        cache_key = cache_manager.generate_key("gap_analysis", ticker)
        cached = cache_manager.get("realtime", cache_key)
        if cached:
            return cached
        
        # Get recent data
        hist_data = yahoo_client.get_historical_data(ticker, period="5d", interval="1d")
        if "error" in hist_data:
            raise DataUnavailableError(f"Tidak dapat mengambil data untuk {ticker}")
        
        if not hist_data.get("data") or len(hist_data["data"]) < 2:
            raise DataUnavailableError(f"Data tidak cukup untuk analisis gap {ticker}")
        
        # Get data
        df = pd.DataFrame(hist_data["data"])
        df = df.sort_values("date")
        
        # Yesterday and today
        yesterday = df.iloc[-2]
        today = df.iloc[-1]
        
        prev_close = float(yesterday["close"])
        prev_high = float(yesterday["high"])
        prev_low = float(yesterday["low"])
        today_open = float(today["open"])
        today_high = float(today["high"])
        today_low = float(today["low"])
        
        # Get current price
        price_data = yahoo_client.get_current_price(ticker)
        current_price = price_data.get("price", float(today["close"]))
        
        # Calculate gap
        gap_size = today_open - prev_close
        gap_percent = (gap_size / prev_close * 100) if prev_close > 0 else 0
        
        # Determine gap type
        if abs(gap_percent) < 0.5:
            gap_type = "no_gap"
            gap_description = "No significant gap"
        elif gap_size > 0:
            if gap_percent >= 5:
                gap_type = "big_gap_up"
                gap_description = "🚀 Big Gap Up (>5%)"
            elif gap_percent >= 2:
                gap_type = "gap_up"
                gap_description = "🟢 Gap Up (2-5%)"
            else:
                gap_type = "small_gap_up"
                gap_description = "🟡 Small Gap Up (<2%)"
        else:
            if gap_percent <= -5:
                gap_type = "big_gap_down"
                gap_description = "💥 Big Gap Down (>5%)"
            elif gap_percent <= -2:
                gap_type = "gap_down"
                gap_description = "🔴 Gap Down (2-5%)"
            else:
                gap_type = "small_gap_down"
                gap_description = "🟡 Small Gap Down (<2%)"
        
        # Check if gap is filled
        gap_fill_level = prev_close
        if gap_size > 0:
            # Gap up - filled if price went down to prev close
            gap_filled = today_low <= prev_close
            fill_progress = max(0, min(100, (today_open - today_low) / gap_size * 100)) if gap_size > 0 else 0
        else:
            # Gap down - filled if price went up to prev close
            gap_filled = today_high >= prev_close
            fill_progress = max(0, min(100, (today_high - today_open) / abs(gap_size) * 100)) if gap_size < 0 else 0
        
        # Trading implications
        if gap_type == "no_gap":
            trading_implication = "Normal open - no gap strategy applicable"
            strategy = None
        elif gap_filled:
            trading_implication = "Gap sudah filled - watch for continuation or reversal"
            strategy = "Gap filled, look for next move direction"
        elif gap_size > 0:
            trading_implication = "Gap up unfilled - potential fill or continuation"
            strategy = f"Gap fill target: Rp {prev_close:,.0f} | Continuation above: Rp {today_high:,.0f}"
        else:
            trading_implication = "Gap down unfilled - potential fill or continuation"
            strategy = f"Gap fill target: Rp {prev_close:,.0f} | Continuation below: Rp {today_low:,.0f}"
        
        # True gap analysis (no overlap with previous range)
        is_true_gap_up = today_low > prev_high
        is_true_gap_down = today_high < prev_low
        true_gap = is_true_gap_up or is_true_gap_down
        
        result = {
            "ticker": ticker,
            "name": price_data.get("name", ""),
            "current_price": round(current_price, 2),
            "gap_analysis": {
                "gap_type": gap_type,
                "gap_description": gap_description,
                "gap_size": round(gap_size, 2),
                "gap_percent": round(gap_percent, 2),
                "previous_close": round(prev_close, 2),
                "today_open": round(today_open, 2),
            },
            "gap_fill_status": {
                "is_filled": gap_filled,
                "fill_level": round(gap_fill_level, 2),
                "fill_progress_percent": round(fill_progress, 1),
            },
            "true_gap": {
                "is_true_gap": true_gap,
                "description": "True Gap (no overlap with previous range)" if true_gap else "Common Gap (overlaps with previous range)",
            },
            "today_range": {
                "open": round(today_open, 2),
                "high": round(today_high, 2),
                "low": round(today_low, 2),
                "current": round(current_price, 2),
            },
            "yesterday_range": {
                "high": round(prev_high, 2),
                "low": round(prev_low, 2),
                "close": round(prev_close, 2),
            },
            "trading_implication": trading_implication,
            "strategy": strategy,
            "insights": [
                gap_description,
                f"Gap Size: Rp {gap_size:,.0f} ({gap_percent:+.2f}%)",
                f"Gap Fill Status: {'✅ Filled' if gap_filled else f'❌ Not filled ({fill_progress:.0f}% progress)'}",
                f"True Gap: {'Yes' if true_gap else 'No (common gap)'}",
            ],
        }
        
        # Cache result
        cache_manager.set("realtime", cache_key, result)
        
        return result
        
    except ValueError as e:
        raise InvalidParameterError(str(e))
    except YahooFinanceError as e:
        raise DataUnavailableError(str(e))
    except (InvalidParameterError, DataUnavailableError):
        raise
    except Exception as e:
        raise NetworkError(f"Gagal menganalisis gap: {str(e)}")

