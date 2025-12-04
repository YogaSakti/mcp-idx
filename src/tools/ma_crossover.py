"""Moving Average Crossover detection tool for Indonesian stocks."""

from typing import Any, Dict, List, Optional
from mcp.types import Tool
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta

from src.utils.yahoo import yahoo_client, YahooFinanceError
from src.utils.validators import validate_ticker, validate_period


def get_ma_crossover_tool() -> Tool:
    """Return the MCP tool definition for MA crossover detection."""
    return Tool(
        name="get_ma_crossovers",
        description=(
            "Detect Moving Average crossovers (Golden Cross, Death Cross, EMA crossovers) "
            "untuk Indonesian stocks. Includes SMA 20/50, SMA 50/200, EMA 9/21, EMA 12/26, "
            "MA distance analysis, and signal strength rating."
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
                    "description": "Data period: 3mo, 6mo, 1y (default: 6mo)",
                    "default": "6mo",
                },
                "lookback_days": {
                    "type": "integer",
                    "description": "Days to look back for crossovers (default: 30)",
                    "default": 30,
                },
            },
            "required": ["ticker"],
        },
    )


def detect_crossover(
    fast_ma: pd.Series,
    slow_ma: pd.Series,
    dates: pd.DatetimeIndex,
    lookback_days: int = 30
) -> List[Dict[str, Any]]:
    """
    Detect crossovers between two moving averages.

    Args:
        fast_ma: Fast moving average series
        slow_ma: Slow moving average series
        dates: DatetimeIndex for the data
        lookback_days: Number of days to look back

    Returns:
        List of crossover events
    """
    crossovers = []
    cutoff_date = datetime.now() - timedelta(days=lookback_days)

    # Handle None or empty series
    if fast_ma is None or slow_ma is None:
        return crossovers
    
    # Need at least 2 data points to detect crossover
    if len(fast_ma) < 2 or len(slow_ma) < 2:
        return crossovers

    # Iterate through data to find crossovers
    for i in range(1, len(fast_ma)):
        if pd.isna(fast_ma.iloc[i]) or pd.isna(slow_ma.iloc[i]):
            continue
        if pd.isna(fast_ma.iloc[i-1]) or pd.isna(slow_ma.iloc[i-1]):
            continue

        date = dates[i]

        # Skip if outside lookback window
        if date.replace(tzinfo=None) < cutoff_date:
            continue

        # Golden Cross: fast crosses above slow
        if fast_ma.iloc[i-1] < slow_ma.iloc[i-1] and fast_ma.iloc[i] > slow_ma.iloc[i]:
            crossovers.append({
                "type": "golden_cross",
                "date": date.strftime("%Y-%m-%d"),
                "fast_ma_value": round(float(fast_ma.iloc[i]), 2),
                "slow_ma_value": round(float(slow_ma.iloc[i]), 2),
                "signal": "bullish",
            })

        # Death Cross: fast crosses below slow
        elif fast_ma.iloc[i-1] > slow_ma.iloc[i-1] and fast_ma.iloc[i] < slow_ma.iloc[i]:
            crossovers.append({
                "type": "death_cross",
                "date": date.strftime("%Y-%m-%d"),
                "fast_ma_value": round(float(fast_ma.iloc[i]), 2),
                "slow_ma_value": round(float(slow_ma.iloc[i]), 2),
                "signal": "bearish",
            })

    return crossovers


def calculate_ma_distance(price: float, ma_value: float) -> Dict[str, Any]:
    """Calculate distance between price and MA."""
    if pd.isna(ma_value) or ma_value == 0:
        return {"distance_pct": 0, "position": "unknown"}
    
    distance_pct = ((price - ma_value) / ma_value) * 100
    
    if distance_pct > 10:
        position = "far_above"
        status = "🔴 Overbought - Jauh di atas MA"
    elif distance_pct > 5:
        position = "above"
        status = "🟡 Di atas MA"
    elif distance_pct > 0:
        position = "slightly_above"
        status = "🟢 Sedikit di atas MA"
    elif distance_pct > -5:
        position = "slightly_below"
        status = "🟢 Sedikit di bawah MA"
    elif distance_pct > -10:
        position = "below"
        status = "🟡 Di bawah MA"
    else:
        position = "far_below"
        status = "🔴 Oversold - Jauh di bawah MA"
    
    return {
        "distance_pct": round(distance_pct, 2),
        "position": position,
        "status": status
    }


def calculate_signal_strength(
    alignments: Dict[str, str],
    crossovers: Dict[str, List],
    ma_distances: Dict[str, Dict],
    lookback_days: int
) -> Dict[str, Any]:
    """
    Calculate overall signal strength based on MA analysis.
    
    Returns:
        Dictionary with signal strength (0-100) and recommendation
    """
    score = 50  # Start neutral
    factors = []
    
    # Factor 1: MA Alignment (max ±20 points)
    bullish_alignments = sum(1 for v in alignments.values() if v == "bullish")
    bearish_alignments = sum(1 for v in alignments.values() if v == "bearish")
    total_alignments = len(alignments)
    
    if total_alignments > 0:
        alignment_ratio = (bullish_alignments - bearish_alignments) / total_alignments
        score += alignment_ratio * 20
        
        if bullish_alignments == total_alignments:
            factors.append("✅ Semua MA alignment bullish")
        elif bearish_alignments == total_alignments:
            factors.append("⚠️ Semua MA alignment bearish")
        else:
            factors.append(f"🟡 Mixed alignment ({bullish_alignments} bullish, {bearish_alignments} bearish)")
    
    # Factor 2: Recent Crossovers (max ±20 points)
    recent_bullish = 0
    recent_bearish = 0
    
    for ma_type, crosses in crossovers.items():
        for cross in crosses:
            if cross["signal"] == "bullish":
                recent_bullish += 1
            else:
                recent_bearish += 1
    
    crossover_score = (recent_bullish - recent_bearish) * 10
    score += min(20, max(-20, crossover_score))
    
    if recent_bullish > recent_bearish:
        factors.append(f"📈 {recent_bullish} bullish crossover(s) recent")
    elif recent_bearish > recent_bullish:
        factors.append(f"📉 {recent_bearish} bearish crossover(s) recent")
    
    # Factor 3: Price vs MA200 distance (max ±10 points)
    if "sma_200" in ma_distances:
        dist = ma_distances["sma_200"]["distance_pct"]
        if 0 < dist < 10:
            score += 10
            factors.append("🟢 Harga di atas SMA200 (uptrend)")
        elif dist >= 10:
            score += 5  # Too extended
            factors.append("🟡 Harga terlalu jauh dari SMA200")
        elif -10 < dist < 0:
            score -= 5
            factors.append("🟡 Harga di bawah SMA200")
        else:
            score -= 10
            factors.append("🔴 Harga jauh di bawah SMA200 (downtrend)")
    
    # Clamp score to 0-100
    score = max(0, min(100, score))
    
    # Determine signal
    if score >= 70:
        signal = "🟢 STRONG BUY"
        action = "Entry dengan confidence tinggi"
    elif score >= 55:
        signal = "🟢 BUY"
        action = "Entry dengan SL ketat"
    elif score >= 45:
        signal = "🟡 NEUTRAL"
        action = "Wait for confirmation"
    elif score >= 30:
        signal = "🔴 SELL"
        action = "Consider exit atau short"
    else:
        signal = "🔴 STRONG SELL"
        action = "Exit atau hindari buy"
    
    return {
        "score": round(score),
        "signal": signal,
        "action": action,
        "factors": factors
    }


async def get_ma_crossovers(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect MA crossovers for a stock.

    Args:
        args: Dictionary containing:
            - ticker: Stock ticker
            - period: Data period (default: 6mo)
            - lookback_days: Days to look back (default: 30)

    Returns:
        Dictionary containing crossover information
    """
    ticker = args.get("ticker", "").upper()
    period = args.get("period", "6mo")
    lookback_days = args.get("lookback_days", 30)

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

        close = df['Close']
        dates = df.index
        current_price = float(close.iloc[-1])

        # Calculate ALL moving averages (with None handling)
        try:
            sma_20 = ta.sma(close, length=20)
            sma_50 = ta.sma(close, length=50)
            sma_200 = ta.sma(close, length=200) if len(close) >= 200 else None
            ema_9 = ta.ema(close, length=9)
            ema_12 = ta.ema(close, length=12)
            ema_21 = ta.ema(close, length=21)
            ema_26 = ta.ema(close, length=26)
        except Exception:
            sma_20 = sma_50 = sma_200 = ema_9 = ema_12 = ema_21 = ema_26 = None

        result = {
            "ticker": ticker,
            "period": period,
            "lookback_days": lookback_days,
            "current_price": round(current_price, 2),
            "crossovers": {},
        }

        # Detect ALL crossovers
        # 1. SMA 20 x SMA 50 (Short-term trend)
        sma_20_50_cross = detect_crossover(sma_20, sma_50, dates, lookback_days)
        if sma_20_50_cross:
            result["crossovers"]["sma_20_50"] = sma_20_50_cross

        # 2. SMA 50 x SMA 200 (Golden Cross / Death Cross)
        sma_50_200_cross = detect_crossover(sma_50, sma_200, dates, lookback_days)
        if sma_50_200_cross:
            result["crossovers"]["sma_50_200"] = sma_50_200_cross

        # 3. EMA 9 x EMA 21 (Swing trading)
        ema_9_21_cross = detect_crossover(ema_9, ema_21, dates, lookback_days)
        if ema_9_21_cross:
            result["crossovers"]["ema_9_21"] = ema_9_21_cross

        # 4. EMA 12 x EMA 26 (MACD style)
        ema_12_26_cross = detect_crossover(ema_12, ema_26, dates, lookback_days)
        if ema_12_26_cross:
            result["crossovers"]["ema_12_26"] = ema_12_26_cross

        # Current MA values
        current_mas = {}
        ma_list = [
            ("sma_20", sma_20), ("sma_50", sma_50), ("sma_200", sma_200),
            ("ema_9", ema_9), ("ema_12", ema_12), ("ema_21", ema_21), ("ema_26", ema_26)
        ]
        
        for name, ma in ma_list:
            if ma is not None and len(ma) > 0 and not pd.isna(ma.iloc[-1]):
                current_mas[name] = round(float(ma.iloc[-1]), 2)

        result["current_mas"] = current_mas

        # MA Distance Analysis (Price vs each MA)
        ma_distances = {}
        for name, value in current_mas.items():
            ma_distances[name] = calculate_ma_distance(current_price, value)
        
        result["ma_distance"] = ma_distances

        # Current alignment (bullish if fast > slow)
        alignments = {}
        alignment_pairs = [
            ("sma_20_50", "sma_20", "sma_50"),
            ("sma_50_200", "sma_50", "sma_200"),
            ("ema_9_21", "ema_9", "ema_21"),
            ("ema_12_26", "ema_12", "ema_26"),
        ]
        
        for pair_name, fast, slow in alignment_pairs:
            if fast in current_mas and slow in current_mas:
                alignments[pair_name] = "bullish" if current_mas[fast] > current_mas[slow] else "bearish"

        result["current_alignment"] = alignments

        # Calculate Signal Strength
        signal_strength = calculate_signal_strength(
            alignments, 
            result["crossovers"], 
            ma_distances, 
            lookback_days
        )
        result["signal_strength"] = signal_strength

        # Trading insights
        insights = []
        
        # Golden/Death Cross insights
        if sma_50_200_cross:
            latest = sma_50_200_cross[-1]
            if latest["signal"] == "bullish":
                insights.append(f"✅ Golden Cross on {latest['date']} - Major bullish signal!")
            else:
                insights.append(f"⚠️ Death Cross on {latest['date']} - Major bearish signal!")
        
        # Short-term trend (SMA 20/50)
        if sma_20_50_cross:
            latest = sma_20_50_cross[-1]
            signal_type = "bullish" if latest["signal"] == "bullish" else "bearish"
            insights.append(f"📊 SMA 20/50 {signal_type} cross on {latest['date']} - Short-term trend change")
        
        # Swing trading (EMA 9/21)
        if ema_9_21_cross:
            latest = ema_9_21_cross[-1]
            if latest["signal"] == "bullish":
                insights.append(f"📈 EMA 9/21 bullish on {latest['date']} - Swing buy signal")
            else:
                insights.append(f"📉 EMA 9/21 bearish on {latest['date']} - Swing sell signal")

        # MACD style (EMA 12/26)
        if ema_12_26_cross:
            latest = ema_12_26_cross[-1]
            if latest["signal"] == "bullish":
                insights.append(f"📈 EMA 12/26 bullish on {latest['date']} - Momentum bullish")
            else:
                insights.append(f"📉 EMA 12/26 bearish on {latest['date']} - Momentum bearish")

        # MA Distance insights
        if "sma_200" in ma_distances:
            dist_info = ma_distances["sma_200"]
            insights.append(f"📏 Harga {dist_info['distance_pct']}% dari SMA200 - {dist_info['status']}")

        if not any([sma_20_50_cross, sma_50_200_cross, ema_9_21_cross, ema_12_26_cross]):
            insights.append("⚪ No crossovers detected in lookback period")

        result["insights"] = insights

        return result

    except Exception as e:
        return {
            "ticker": ticker,
            "error": str(e),
        }
