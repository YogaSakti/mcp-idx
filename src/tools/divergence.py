"""Tool for detecting price-indicator divergences."""

from typing import Any, Dict, List, Tuple
import pandas as pd
import numpy as np
import pandas_ta as ta
from mcp.types import Tool
from src.utils.yahoo import yahoo_client, YahooFinanceError
from src.utils.validators import validate_ticker, validate_period


def get_divergence_detection_tool() -> Tool:
    """Get divergence detection tool definition."""
    return Tool(
        name="get_divergence_detection",
        description="Detect divergence antara harga dan indikator (RSI, MACD, OBV). Divergence adalah early warning signal untuk potential reversal. Bullish divergence = price lower low tapi indicator higher low. Bearish divergence = price higher high tapi indicator lower high.",
        inputSchema={
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Ticker saham IDX (contoh: BBCA, BBRI, TLKM)",
                },
                "indicators": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Indikator untuk cek divergence (rsi, macd, obv). Default: semua",
                    "default": ["rsi", "macd", "obv"],
                },
                "lookback": {
                    "type": "integer",
                    "description": "Periode lookback untuk mencari divergence (default: 30 hari)",
                    "default": 30,
                },
                "period": {
                    "type": "string",
                    "description": "Periode data untuk analisis (default: 3mo)",
                    "default": "3mo",
                },
            },
            "required": ["ticker"],
        },
    )


def find_pivot_points(
    series: pd.Series, 
    order: int = 5
) -> Tuple[List[int], List[int]]:
    """
    Find pivot highs and pivot lows in a series.
    
    Args:
        series: Price or indicator series
        order: Number of bars on each side to confirm pivot
        
    Returns:
        Tuple of (pivot_high_indices, pivot_low_indices)
    """
    pivot_highs = []
    pivot_lows = []
    
    values = series.values
    
    for i in range(order, len(values) - order):
        # Check for pivot high
        is_pivot_high = True
        for j in range(1, order + 1):
            if values[i] <= values[i - j] or values[i] <= values[i + j]:
                is_pivot_high = False
                break
        if is_pivot_high:
            pivot_highs.append(i)
        
        # Check for pivot low
        is_pivot_low = True
        for j in range(1, order + 1):
            if values[i] >= values[i - j] or values[i] >= values[i + j]:
                is_pivot_low = False
                break
        if is_pivot_low:
            pivot_lows.append(i)
    
    return pivot_highs, pivot_lows


def detect_regular_divergence(
    price: pd.Series,
    indicator: pd.Series,
    lookback: int = 30
) -> List[Dict[str, Any]]:
    """
    Detect regular divergence (reversal signals).
    
    Regular Bullish: Price makes lower low, indicator makes higher low
    Regular Bearish: Price makes higher high, indicator makes lower high
    
    Args:
        price: Close price series
        indicator: Indicator series (RSI, MACD, etc.)
        lookback: Number of bars to look back
        
    Returns:
        List of detected divergences
    """
    divergences = []
    
    # Use recent data only
    price = price.tail(lookback)
    indicator = indicator.tail(lookback)
    
    # Find pivot points
    price_highs, price_lows = find_pivot_points(price, order=3)
    ind_highs, ind_lows = find_pivot_points(indicator, order=3)
    
    # Detect Bullish Divergence (price lower low, indicator higher low)
    if len(price_lows) >= 2:
        for i in range(1, len(price_lows)):
            curr_idx = price_lows[i]
            prev_idx = price_lows[i - 1]
            
            # Price made lower low
            if price.iloc[curr_idx] < price.iloc[prev_idx]:
                # Find corresponding indicator lows
                curr_ind_val = indicator.iloc[curr_idx]
                prev_ind_val = indicator.iloc[prev_idx]
                
                # Indicator made higher low (divergence!)
                if curr_ind_val > prev_ind_val:
                    strength = _calculate_divergence_strength(
                        price.iloc[prev_idx], price.iloc[curr_idx],
                        prev_ind_val, curr_ind_val
                    )
                    divergences.append({
                        "type": "bullish_regular",
                        "signal": "Potential reversal UP",
                        "price_pattern": "lower_low",
                        "indicator_pattern": "higher_low",
                        "start_idx": prev_idx,
                        "end_idx": curr_idx,
                        "start_price": round(float(price.iloc[prev_idx]), 2),
                        "end_price": round(float(price.iloc[curr_idx]), 2),
                        "start_indicator": round(float(prev_ind_val), 2),
                        "end_indicator": round(float(curr_ind_val), 2),
                        "strength": strength,
                        "bars_apart": curr_idx - prev_idx,
                    })
    
    # Detect Bearish Divergence (price higher high, indicator lower high)
    if len(price_highs) >= 2:
        for i in range(1, len(price_highs)):
            curr_idx = price_highs[i]
            prev_idx = price_highs[i - 1]
            
            # Price made higher high
            if price.iloc[curr_idx] > price.iloc[prev_idx]:
                # Find corresponding indicator highs
                curr_ind_val = indicator.iloc[curr_idx]
                prev_ind_val = indicator.iloc[prev_idx]
                
                # Indicator made lower high (divergence!)
                if curr_ind_val < prev_ind_val:
                    strength = _calculate_divergence_strength(
                        price.iloc[prev_idx], price.iloc[curr_idx],
                        prev_ind_val, curr_ind_val
                    )
                    divergences.append({
                        "type": "bearish_regular",
                        "signal": "Potential reversal DOWN",
                        "price_pattern": "higher_high",
                        "indicator_pattern": "lower_high",
                        "start_idx": prev_idx,
                        "end_idx": curr_idx,
                        "start_price": round(float(price.iloc[prev_idx]), 2),
                        "end_price": round(float(price.iloc[curr_idx]), 2),
                        "start_indicator": round(float(prev_ind_val), 2),
                        "end_indicator": round(float(curr_ind_val), 2),
                        "strength": strength,
                        "bars_apart": curr_idx - prev_idx,
                    })
    
    return divergences


def detect_hidden_divergence(
    price: pd.Series,
    indicator: pd.Series,
    lookback: int = 30
) -> List[Dict[str, Any]]:
    """
    Detect hidden divergence (trend continuation signals).
    
    Hidden Bullish: Price makes higher low, indicator makes lower low (uptrend continues)
    Hidden Bearish: Price makes lower high, indicator makes higher high (downtrend continues)
    
    Args:
        price: Close price series
        indicator: Indicator series
        lookback: Number of bars to look back
        
    Returns:
        List of detected divergences
    """
    divergences = []
    
    # Use recent data only
    price = price.tail(lookback)
    indicator = indicator.tail(lookback)
    
    # Find pivot points
    price_highs, price_lows = find_pivot_points(price, order=3)
    ind_highs, ind_lows = find_pivot_points(indicator, order=3)
    
    # Detect Hidden Bullish (price higher low, indicator lower low - uptrend continues)
    if len(price_lows) >= 2:
        for i in range(1, len(price_lows)):
            curr_idx = price_lows[i]
            prev_idx = price_lows[i - 1]
            
            # Price made higher low (uptrend)
            if price.iloc[curr_idx] > price.iloc[prev_idx]:
                curr_ind_val = indicator.iloc[curr_idx]
                prev_ind_val = indicator.iloc[prev_idx]
                
                # Indicator made lower low
                if curr_ind_val < prev_ind_val:
                    strength = _calculate_divergence_strength(
                        price.iloc[prev_idx], price.iloc[curr_idx],
                        prev_ind_val, curr_ind_val
                    )
                    divergences.append({
                        "type": "bullish_hidden",
                        "signal": "Uptrend likely to continue",
                        "price_pattern": "higher_low",
                        "indicator_pattern": "lower_low",
                        "start_idx": prev_idx,
                        "end_idx": curr_idx,
                        "start_price": round(float(price.iloc[prev_idx]), 2),
                        "end_price": round(float(price.iloc[curr_idx]), 2),
                        "start_indicator": round(float(prev_ind_val), 2),
                        "end_indicator": round(float(curr_ind_val), 2),
                        "strength": strength,
                        "bars_apart": curr_idx - prev_idx,
                    })
    
    # Detect Hidden Bearish (price lower high, indicator higher high - downtrend continues)
    if len(price_highs) >= 2:
        for i in range(1, len(price_highs)):
            curr_idx = price_highs[i]
            prev_idx = price_highs[i - 1]
            
            # Price made lower high (downtrend)
            if price.iloc[curr_idx] < price.iloc[prev_idx]:
                curr_ind_val = indicator.iloc[curr_idx]
                prev_ind_val = indicator.iloc[prev_idx]
                
                # Indicator made higher high
                if curr_ind_val > prev_ind_val:
                    strength = _calculate_divergence_strength(
                        price.iloc[prev_idx], price.iloc[curr_idx],
                        prev_ind_val, curr_ind_val
                    )
                    divergences.append({
                        "type": "bearish_hidden",
                        "signal": "Downtrend likely to continue",
                        "price_pattern": "lower_high",
                        "indicator_pattern": "higher_high",
                        "start_idx": prev_idx,
                        "end_idx": curr_idx,
                        "start_price": round(float(price.iloc[prev_idx]), 2),
                        "end_price": round(float(price.iloc[curr_idx]), 2),
                        "start_indicator": round(float(prev_ind_val), 2),
                        "end_indicator": round(float(curr_ind_val), 2),
                        "strength": strength,
                        "bars_apart": curr_idx - prev_idx,
                    })
    
    return divergences


def _calculate_divergence_strength(
    price1: float, price2: float,
    ind1: float, ind2: float
) -> str:
    """Calculate the strength of divergence based on magnitude."""
    price_change = abs((price2 - price1) / price1) * 100 if price1 != 0 else 0
    ind_change = abs((ind2 - ind1) / ind1) * 100 if ind1 != 0 else 0
    
    # Average of both changes
    avg_change = (price_change + ind_change) / 2
    
    if avg_change > 10:
        return "strong"
    elif avg_change > 5:
        return "moderate"
    else:
        return "weak"


def analyze_indicator_divergence(
    df: pd.DataFrame,
    indicator_name: str,
    lookback: int = 30
) -> Dict[str, Any]:
    """
    Analyze divergence for a specific indicator.
    
    Args:
        df: DataFrame with OHLCV data
        indicator_name: Name of indicator (rsi, macd, obv)
        lookback: Lookback period
        
    Returns:
        Dictionary with divergence analysis for the indicator
    """
    close = df['Close']
    
    # Calculate indicator
    indicator = None
    indicator_value = None
    
    if indicator_name == "rsi":
        indicator = ta.rsi(close, length=14)
        if indicator is not None and not indicator.empty and pd.notna(indicator.iloc[-1]):
            indicator_value = round(float(indicator.iloc[-1]), 2)
            
    elif indicator_name == "macd":
        macd_data = ta.macd(close)
        if macd_data is not None and not macd_data.empty:
            # Use MACD histogram for divergence
            indicator = macd_data.iloc[:, 2]  # Histogram column
            if pd.notna(indicator.iloc[-1]):
                indicator_value = round(float(indicator.iloc[-1]), 4)
                
    elif indicator_name == "obv":
        indicator = ta.obv(close, df['Volume'])
        if indicator is not None and not indicator.empty and pd.notna(indicator.iloc[-1]):
            # Normalize OBV for easier reading
            indicator_value = round(float(indicator.iloc[-1]), 0)
    
    if indicator is None or indicator.empty:
        return {
            "indicator": indicator_name,
            "current_value": None,
            "regular_divergences": [],
            "hidden_divergences": [],
            "active_divergence": None,
            "error": f"Could not calculate {indicator_name}"
        }
    
    # Detect divergences
    regular = detect_regular_divergence(close, indicator, lookback)
    hidden = detect_hidden_divergence(close, indicator, lookback)
    
    # Find most recent/active divergence
    all_divs = regular + hidden
    active_divergence = None
    
    if all_divs:
        # Sort by end_idx (most recent first)
        all_divs_sorted = sorted(all_divs, key=lambda x: x['end_idx'], reverse=True)
        
        # Check if most recent divergence is still "active" (within last 5 bars)
        most_recent = all_divs_sorted[0]
        if most_recent['end_idx'] >= lookback - 5:  # Within last 5 bars
            active_divergence = most_recent
    
    return {
        "indicator": indicator_name.upper(),
        "current_value": indicator_value,
        "regular_divergences": regular,
        "hidden_divergences": hidden,
        "total_divergences": len(regular) + len(hidden),
        "active_divergence": active_divergence,
    }


def generate_overall_signal(analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate overall signal from all indicator analyses.
    
    Args:
        analyses: List of indicator analyses
        
    Returns:
        Dictionary with overall signal
    """
    bullish_signals = 0
    bearish_signals = 0
    active_divergences = []
    
    for analysis in analyses:
        if analysis.get('active_divergence'):
            div = analysis['active_divergence']
            active_divergences.append({
                "indicator": analysis['indicator'],
                "type": div['type'],
                "signal": div['signal'],
                "strength": div['strength'],
            })
            
            if 'bullish' in div['type']:
                if div['strength'] == 'strong':
                    bullish_signals += 2
                else:
                    bullish_signals += 1
            elif 'bearish' in div['type']:
                if div['strength'] == 'strong':
                    bearish_signals += 2
                else:
                    bearish_signals += 1
    
    # Determine overall signal
    if not active_divergences:
        signal = "no_divergence"
        action = "no_action"
        confidence = "n/a"
    elif bullish_signals > bearish_signals:
        if bullish_signals >= 3:
            signal = "strong_bullish_divergence"
            action = "consider_buy"
            confidence = "high"
        else:
            signal = "bullish_divergence"
            action = "watch_for_reversal_up"
            confidence = "medium"
    elif bearish_signals > bullish_signals:
        if bearish_signals >= 3:
            signal = "strong_bearish_divergence"
            action = "consider_sell"
            confidence = "high"
        else:
            signal = "bearish_divergence"
            action = "watch_for_reversal_down"
            confidence = "medium"
    else:
        signal = "mixed_divergence"
        action = "wait_for_clarity"
        confidence = "low"
    
    # Count agreement
    indicator_agreement = len(set(d['type'].split('_')[0] for d in active_divergences))
    
    return {
        "signal": signal,
        "action": action,
        "confidence": confidence,
        "bullish_score": bullish_signals,
        "bearish_score": bearish_signals,
        "active_divergences": active_divergences,
        "indicators_with_divergence": len(active_divergences),
        "indicator_agreement": "aligned" if indicator_agreement == 1 else "mixed",
    }


async def get_divergence_detection(arguments: dict) -> Dict[str, Any]:
    """
    Main handler for divergence detection tool.
    
    Args:
        arguments: Tool arguments
        
    Returns:
        Dictionary with divergence detection results
    """
    ticker = validate_ticker(arguments.get("ticker", ""))
    indicators = arguments.get("indicators", ["rsi", "macd", "obv"])
    lookback = arguments.get("lookback", 30)
    period = validate_period(arguments.get("period", "3mo"))
    
    # Validate indicators
    valid_indicators = ["rsi", "macd", "obv"]
    indicators = [ind.lower() for ind in indicators if ind.lower() in valid_indicators]
    
    if not indicators:
        indicators = valid_indicators
    
    # Ensure reasonable lookback
    if lookback < 15:
        lookback = 15
    if lookback > 60:
        lookback = 60
    
    try:
        # Fetch historical data
        stock = yahoo_client.get_ticker(ticker)
        df = stock.history(period=period, interval="1d")
        
        if df.empty:
            raise YahooFinanceError(f"No data available for {ticker}")
        
        # Ensure data is sorted by date
        df.sort_index(inplace=True)
        
        # Need enough data for indicators
        min_bars = max(lookback + 20, 50)
        if len(df) < min_bars:
            raise YahooFinanceError(
                f"Insufficient data for {ticker}. Need {min_bars} bars, got {len(df)}"
            )
        
        # Analyze each indicator
        analyses = []
        for ind in indicators:
            analysis = analyze_indicator_divergence(df, ind, lookback)
            analyses.append(analysis)
        
        # Generate overall signal
        overall = generate_overall_signal(analyses)
        
        # Get current price info
        current = df.iloc[-1]
        prev_close = float(df.iloc[-2]['Close'])
        price_change = float(current['Close']) - prev_close
        price_change_pct = (price_change / prev_close) * 100 if prev_close > 0 else 0
        
        # Build insights
        insights = []
        
        if overall['signal'] == "no_divergence":
            insights.append("📊 No active divergence detected")
            insights.append("Price and indicators are moving in harmony")
            
        elif "bullish" in overall['signal']:
            insights.append("🟢 BULLISH DIVERGENCE DETECTED!")
            insights.append("Price making lows while momentum is building")
            insights.append("This often precedes upward reversals")
            if overall['confidence'] == "high":
                insights.append("⚡ Multiple indicators confirm - high probability setup")
                
        elif "bearish" in overall['signal']:
            insights.append("🔴 BEARISH DIVERGENCE DETECTED!")
            insights.append("Price making highs while momentum is weakening")
            insights.append("This often precedes downward reversals")
            if overall['confidence'] == "high":
                insights.append("⚡ Multiple indicators confirm - high probability setup")
                
        else:  # mixed
            insights.append("⚠️ Mixed signals from different indicators")
            insights.append("Wait for clearer confirmation before acting")
        
        # Add specific divergence details
        for div in overall['active_divergences']:
            insights.append(f"  → {div['indicator']}: {div['type']} ({div['strength']})")
        
        return {
            "ticker": ticker,
            "analysis_date": str(df.index[-1].date()),
            "current_price": round(float(current['Close']), 2),
            "price_change": round(price_change, 2),
            "price_change_pct": round(price_change_pct, 2),
            "indicator_analyses": analyses,
            "overall_signal": overall,
            "insights": insights,
            "parameters": {
                "indicators_checked": indicators,
                "lookback_days": lookback,
                "period": period,
            },
            "educational_note": {
                "regular_divergence": "Predicts trend REVERSAL. Bullish: price lower low + indicator higher low. Bearish: price higher high + indicator lower high.",
                "hidden_divergence": "Predicts trend CONTINUATION. Bullish: price higher low + indicator lower low. Bearish: price lower high + indicator higher high.",
                "best_practice": "Combine with other signals (support/resistance, volume, candlestick patterns) for confirmation."
            }
        }
        
    except YahooFinanceError as e:
        raise
    except Exception as e:
        raise YahooFinanceError(f"Error analyzing divergence for {ticker}: {str(e)}")

