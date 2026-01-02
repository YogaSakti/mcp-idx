"""Tool for detecting price breakouts."""

from typing import Any, Dict
import pandas as pd
import numpy as np
import pandas_ta as ta
from mcp.types import Tool
from src.utils.yahoo import yahoo_client, YahooFinanceError
from src.utils.validators import validate_ticker, validate_period


def get_breakout_detection_tool() -> Tool:
    """Get breakout detection tool definition."""
    return Tool(
        name="get_breakout_detection",
        description="Detect price breakout dari consolidation range. Mengidentifikasi breakout resistance/support dengan volume confirmation, target price, dan stop loss. Berguna untuk entry signal momentum trading.",
        inputSchema={
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Ticker saham IDX (contoh: BBCA, BBRI, TLKM)",
                },
                "lookback": {
                    "type": "integer",
                    "description": "Periode lookback untuk consolidation range (default: 20 hari)",
                    "default": 20,
                },
                "period": {
                    "type": "string",
                    "description": "Periode data untuk analisis (default: 3mo)",
                    "default": "3mo",
                },
                "volume_threshold": {
                    "type": "number",
                    "description": "Volume multiplier untuk konfirmasi breakout (default: 1.5x average)",
                    "default": 1.5,
                },
            },
            "required": ["ticker"],
        },
    )


def calculate_atr(df: pd.DataFrame, period: int = 14) -> float:
    """
    Calculate ATR (Average True Range) for the given data.
    
    Args:
        df: DataFrame with High, Low, Close columns
        period: ATR period (default: 14)
        
    Returns:
        Current ATR value
    """
    if df.empty or len(df) < period:
        return 0.0
    
    atr = ta.atr(df['High'], df['Low'], df['Close'], length=period)
    if atr is None or atr.empty:
        return 0.0
    
    atr_value = atr.iloc[-1]
    return float(atr_value) if pd.notna(atr_value) else 0.0


def find_consolidation_range(df: pd.DataFrame, lookback: int = 20, atr: float = 0.0) -> Dict[str, Any]:
    """
    Find consolidation range (support and resistance levels).
    Uses ATR-based threshold for consolidation detection.
    
    Args:
        df: DataFrame with OHLCV data
        lookback: Number of days to look back
        atr: Current ATR value for volatility-adjusted thresholds
        
    Returns:
        Dictionary with support, resistance, and range info
    """
    recent = df.tail(lookback)
    
    # Get high and low of consolidation range
    resistance = float(recent['High'].max())
    support = float(recent['Low'].min())
    
    # Calculate range metrics
    range_size = resistance - support
    range_pct = (range_size / support) * 100 if support > 0 else 0
    
    # Average price in range
    avg_price = float(recent['Close'].mean())
    
    # ATR-based consolidation detection
    # If range is less than 3x ATR, it's consolidating (tight range relative to volatility)
    # This adapts to each stock's volatility:
    # - Low volatility stock (1% ATR): consolidation if range < 3%
    # - High volatility stock (5% ATR): consolidation if range < 15%
    if atr > 0 and avg_price > 0:
        atr_percent = (atr / avg_price) * 100
        consolidation_threshold_pct = atr_percent * 3  # Range should be < 3x ATR%
        is_consolidating = range_pct < consolidation_threshold_pct
        consolidation_threshold = consolidation_threshold_pct
    else:
        # Fallback to fixed 15% if ATR not available
        is_consolidating = range_pct < 15
        consolidation_threshold = 15.0
    
    # Find pivot points within the range
    pivot_highs = []
    pivot_lows = []
    
    for i in range(2, len(recent) - 2):
        # Pivot high: higher than 2 bars before and after
        if (recent['High'].iloc[i] > recent['High'].iloc[i-1] and 
            recent['High'].iloc[i] > recent['High'].iloc[i-2] and
            recent['High'].iloc[i] > recent['High'].iloc[i+1] and 
            recent['High'].iloc[i] > recent['High'].iloc[i+2]):
            pivot_highs.append(float(recent['High'].iloc[i]))
        
        # Pivot low: lower than 2 bars before and after
        if (recent['Low'].iloc[i] < recent['Low'].iloc[i-1] and 
            recent['Low'].iloc[i] < recent['Low'].iloc[i-2] and
            recent['Low'].iloc[i] < recent['Low'].iloc[i+1] and 
            recent['Low'].iloc[i] < recent['Low'].iloc[i+2]):
            pivot_lows.append(float(recent['Low'].iloc[i]))
    
    # Refined levels from pivot points
    refined_resistance = np.mean(pivot_highs) if pivot_highs else resistance
    refined_support = np.mean(pivot_lows) if pivot_lows else support
    
    return {
        "resistance": round(resistance, 2),
        "support": round(support, 2),
        "refined_resistance": round(refined_resistance, 2),
        "refined_support": round(refined_support, 2),
        "range_size": round(range_size, 2),
        "range_pct": round(range_pct, 2),
        "avg_price": round(avg_price, 2),
        "is_consolidating": is_consolidating,
        "consolidation_threshold_pct": round(consolidation_threshold, 2),
        "pivot_highs_count": len(pivot_highs),
        "pivot_lows_count": len(pivot_lows),
    }


def detect_breakout(
    df: pd.DataFrame,
    consolidation: Dict[str, Any],
    volume_threshold: float = 1.5,
    atr: float = 0.0
) -> Dict[str, Any]:
    """
    Detect if a breakout has occurred.
    Uses ATR-based thresholds for breakout strength and stop loss.
    
    Args:
        df: DataFrame with OHLCV data
        consolidation: Consolidation range info
        volume_threshold: Volume multiplier for confirmation
        atr: Current ATR value for volatility-adjusted thresholds
        
    Returns:
        Dictionary with breakout detection results
    """
    current = df.iloc[-1]
    prev = df.iloc[-2]
    
    current_close = float(current['Close'])
    current_high = float(current['High'])
    current_low = float(current['Low'])
    current_volume = float(current['Volume'])
    
    resistance = consolidation['resistance']
    support = consolidation['support']
    refined_resistance = consolidation['refined_resistance']
    refined_support = consolidation['refined_support']
    
    # Calculate average volume (20-day)
    avg_volume = float(df['Volume'].tail(20).mean())
    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
    volume_confirmed = volume_ratio >= volume_threshold
    
    # Determine breakout status
    breakout_type = None
    breakout_price = None
    breakout_strength = "none"
    atr_multiple = 0.0
    
    # ATR-based testing threshold (within 0.5 ATR of level)
    # Fallback to 1% if ATR not available
    if atr > 0:
        testing_threshold = atr * 0.5
    else:
        testing_threshold = resistance * 0.01  # 1% fallback
    
    # Resistance breakout (bullish)
    if current_close > resistance:
        breakout_type = "resistance_breakout"
        breakout_price = resistance
        
        # Calculate strength based on ATR (volatility-adjusted)
        breakout_distance = current_close - resistance
        
        if atr > 0:
            atr_multiple = breakout_distance / atr
            # Strong: >= 1 ATR above resistance with volume
            # Moderate: >= 0.5 ATR above OR volume confirmed
            # Weak: < 0.5 ATR and no volume
            if atr_multiple >= 1.0 and volume_confirmed:
                breakout_strength = "strong"
            elif atr_multiple >= 0.5 or volume_confirmed:
                breakout_strength = "moderate"
            else:
                breakout_strength = "weak"
        else:
            # Fallback to percentage-based if ATR not available
            pct_above = ((current_close - resistance) / resistance) * 100
            if pct_above > 3 and volume_confirmed:
                breakout_strength = "strong"
            elif pct_above > 1 or volume_confirmed:
                breakout_strength = "moderate"
            else:
                breakout_strength = "weak"
            
    # Support breakdown (bearish)
    elif current_close < support:
        breakout_type = "support_breakdown"
        breakout_price = support
        
        # Calculate strength based on ATR (volatility-adjusted)
        breakdown_distance = support - current_close
        
        if atr > 0:
            atr_multiple = breakdown_distance / atr
            if atr_multiple >= 1.0 and volume_confirmed:
                breakout_strength = "strong"
            elif atr_multiple >= 0.5 or volume_confirmed:
                breakout_strength = "moderate"
            else:
                breakout_strength = "weak"
        else:
            # Fallback to percentage-based
            pct_below = ((support - current_close) / support) * 100
            if pct_below > 3 and volume_confirmed:
                breakout_strength = "strong"
            elif pct_below > 1 or volume_confirmed:
                breakout_strength = "moderate"
            else:
                breakout_strength = "weak"
            
    # Testing resistance (potential breakout) - within 0.5 ATR
    elif current_high >= resistance - testing_threshold:
        breakout_type = "testing_resistance"
        breakout_price = resistance
        breakout_strength = "pending"
        
    # Testing support (potential breakdown) - within 0.5 ATR
    elif current_low <= support + testing_threshold:
        breakout_type = "testing_support"
        breakout_price = support
        breakout_strength = "pending"
        
    # Inside range
    else:
        breakout_type = "inside_range"
        breakout_strength = "none"
    
    # Calculate targets and stop loss
    range_size = consolidation['range_size']
    
    targets = {}
    stop_loss = None
    
    # ATR-based stop loss multiplier (1.5x ATR is standard for breakout trades)
    # Fallback to 2% if ATR not available
    if atr > 0:
        stop_distance = atr * 1.5
    else:
        stop_distance = None  # Will use percentage fallback
    
    if breakout_type == "resistance_breakout":
        # Target: range projection above breakout
        targets = {
            "target_1": round(resistance + (range_size * 0.618), 2),  # 61.8% of range
            "target_2": round(resistance + range_size, 2),           # 100% of range
            "target_3": round(resistance + (range_size * 1.618), 2), # 161.8% of range
        }
        # ATR-based stop loss: 1.5x ATR below breakout level
        if stop_distance:
            stop_loss = round(resistance - stop_distance, 2)
        else:
            stop_loss = round(resistance * 0.98, 2)  # 2% fallback
        
    elif breakout_type == "support_breakdown":
        # Target: range projection below breakdown
        targets = {
            "target_1": round(support - (range_size * 0.618), 2),
            "target_2": round(support - range_size, 2),
            "target_3": round(support - (range_size * 1.618), 2),
        }
        # ATR-based stop loss: 1.5x ATR above breakdown level
        if stop_distance:
            stop_loss = round(support + stop_distance, 2)
        else:
            stop_loss = round(support * 1.02, 2)  # 2% fallback
        
    elif breakout_type == "testing_resistance":
        targets = {
            "potential_target": round(resistance + range_size, 2),
        }
        stop_loss = round(support, 2)
        
    elif breakout_type == "testing_support":
        targets = {
            "potential_target": round(support - range_size, 2),
        }
        stop_loss = round(resistance, 2)
    
    # Risk/Reward calculation
    risk_reward = None
    if targets and stop_loss and breakout_type in ["resistance_breakout", "support_breakdown"]:
        if breakout_type == "resistance_breakout":
            risk = current_close - stop_loss
            reward = targets.get("target_2", targets.get("target_1", current_close)) - current_close
        else:
            risk = stop_loss - current_close
            reward = current_close - targets.get("target_2", targets.get("target_1", current_close))
        
        if risk > 0:
            risk_reward = round(reward / risk, 2)
    
    return {
        "breakout_type": breakout_type,
        "breakout_price": breakout_price,
        "breakout_strength": breakout_strength,
        "atr_multiple": round(atr_multiple, 2) if atr_multiple > 0 else None,
        "current_price": round(current_close, 2),
        "volume_ratio": round(volume_ratio, 2),
        "volume_confirmed": volume_confirmed,
        "avg_volume": round(avg_volume, 0),
        "current_volume": round(current_volume, 0),
        "targets": targets,
        "stop_loss": stop_loss,
        "stop_loss_method": "ATR-based (1.5x ATR)" if atr > 0 else "Percentage-based (2%)",
        "risk_reward_ratio": risk_reward,
    }


def check_false_breakout(df: pd.DataFrame, consolidation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check for signs of false breakout (failed breakout that reverses).
    
    Args:
        df: DataFrame with OHLCV data
        consolidation: Consolidation range info
        
    Returns:
        Dictionary with false breakout indicators
    """
    if len(df) < 5:
        return {"has_warning": False, "warnings": []}
    
    warnings = []
    recent_5 = df.tail(5)
    
    resistance = consolidation['resistance']
    support = consolidation['support']
    
    # Check for resistance rejection (went above but closed below)
    for i in range(len(recent_5)):
        row = recent_5.iloc[i]
        if row['High'] > resistance and row['Close'] < resistance:
            warnings.append("Rejection at resistance (upper wick)")
            break
    
    # Check for support rejection (went below but closed above)
    for i in range(len(recent_5)):
        row = recent_5.iloc[i]
        if row['Low'] < support and row['Close'] > support:
            warnings.append("Rejection at support (lower wick)")
            break
    
    # Check for decreasing volume on breakout attempt
    if len(recent_5) >= 3:
        recent_volumes = recent_5['Volume'].values[-3:]
        if recent_volumes[-1] < recent_volumes[-2] < recent_volumes[-3]:
            warnings.append("Decreasing volume on recent bars (weak momentum)")
    
    # Check for long wicks (indecision)
    current = df.iloc[-1]
    body = abs(current['Close'] - current['Open'])
    total_range = current['High'] - current['Low']
    if total_range > 0 and body / total_range < 0.3:
        warnings.append("Long wicks indicate indecision")
    
    return {
        "has_warning": len(warnings) > 0,
        "warnings": warnings,
        "warning_count": len(warnings),
    }


def generate_signal(breakout: Dict[str, Any], false_breakout: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate trading signal based on breakout analysis.
    
    Args:
        breakout: Breakout detection results
        false_breakout: False breakout warnings
        
    Returns:
        Dictionary with signal and recommendation
    """
    breakout_type = breakout['breakout_type']
    strength = breakout['breakout_strength']
    volume_confirmed = breakout['volume_confirmed']
    has_warning = false_breakout['has_warning']
    
    signal = "neutral"
    action = "wait"
    confidence = "low"
    
    if breakout_type == "resistance_breakout":
        if strength == "strong" and volume_confirmed and not has_warning:
            signal = "strong_bullish"
            action = "buy"
            confidence = "high"
        elif strength == "moderate" and not has_warning:
            signal = "bullish"
            action = "buy_on_pullback"
            confidence = "medium"
        elif strength == "weak" or has_warning:
            signal = "weak_bullish"
            action = "wait_confirmation"
            confidence = "low"
            
    elif breakout_type == "support_breakdown":
        if strength == "strong" and volume_confirmed and not has_warning:
            signal = "strong_bearish"
            action = "sell"
            confidence = "high"
        elif strength == "moderate" and not has_warning:
            signal = "bearish"
            action = "reduce_position"
            confidence = "medium"
        elif strength == "weak" or has_warning:
            signal = "weak_bearish"
            action = "wait_confirmation"
            confidence = "low"
            
    elif breakout_type == "testing_resistance":
        signal = "potential_bullish"
        action = "prepare_buy"
        confidence = "pending"
        
    elif breakout_type == "testing_support":
        signal = "potential_bearish"
        action = "prepare_sell"
        confidence = "pending"
        
    else:  # inside_range
        signal = "neutral"
        action = "wait"
        confidence = "n/a"
    
    return {
        "signal": signal,
        "action": action,
        "confidence": confidence,
    }


async def get_breakout_detection(arguments: dict) -> Dict[str, Any]:
    """
    Main handler for breakout detection tool.
    
    Args:
        arguments: Tool arguments
        
    Returns:
        Dictionary with breakout detection results
    """
    ticker = validate_ticker(arguments.get("ticker", ""))
    lookback = arguments.get("lookback", 20)
    period = validate_period(arguments.get("period", "3mo"))
    volume_threshold = arguments.get("volume_threshold", 1.5)
    
    # Ensure minimum lookback
    if lookback < 10:
        lookback = 10
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
        
        # Need at least lookback + 5 days for analysis
        min_bars = lookback + 5
        if len(df) < min_bars:
            raise YahooFinanceError(
                f"Insufficient data for {ticker}. Need {min_bars} bars, got {len(df)}"
            )
        
        # Calculate ATR for volatility-adjusted thresholds
        atr = calculate_atr(df, period=14)
        
        # Find consolidation range with ATR-based threshold
        consolidation = find_consolidation_range(df, lookback, atr)
        
        # Detect breakout with ATR-based thresholds
        breakout = detect_breakout(df, consolidation, volume_threshold, atr)
        
        # Check for false breakout warnings
        false_breakout = check_false_breakout(df, consolidation)
        
        # Generate signal
        signal_result = generate_signal(breakout, false_breakout)
        
        # Get current price info
        current = df.iloc[-1]
        prev_close = float(df.iloc[-2]['Close'])
        price_change = float(current['Close']) - prev_close
        price_change_pct = (price_change / prev_close) * 100 if prev_close > 0 else 0
        
        # Build insights
        insights = []
        
        if breakout['breakout_type'] == "resistance_breakout":
            insights.append(f"🚀 BREAKOUT! Price closed above resistance {consolidation['resistance']}")
            if breakout['volume_confirmed']:
                insights.append("✅ Volume confirmation: Strong institutional interest")
            else:
                insights.append("⚠️ Low volume: Watch for false breakout")
                
        elif breakout['breakout_type'] == "support_breakdown":
            insights.append(f"🔻 BREAKDOWN! Price closed below support {consolidation['support']}")
            if breakout['volume_confirmed']:
                insights.append("⚠️ Volume confirmation: Strong selling pressure")
            else:
                insights.append("📊 Low volume: May be temporary weakness")
                
        elif breakout['breakout_type'] == "testing_resistance":
            insights.append(f"👀 Testing resistance at {consolidation['resistance']}")
            insights.append("Prepare for potential breakout if volume increases")
            
        elif breakout['breakout_type'] == "testing_support":
            insights.append(f"👀 Testing support at {consolidation['support']}")
            insights.append("Watch for bounce or breakdown")
            
        else:
            insights.append(f"📊 Trading inside range ({consolidation['support']} - {consolidation['resistance']})")
            if consolidation['is_consolidating']:
                insights.append("Consolidation pattern detected - breakout may be imminent")
        
        # Add warnings
        if false_breakout['has_warning']:
            insights.append("⚠️ Warning signs detected:")
            for warning in false_breakout['warnings']:
                insights.append(f"  - {warning}")
        
        return {
            "ticker": ticker,
            "analysis_date": str(df.index[-1].date()),
            "current_price": round(float(current['Close']), 2),
            "price_change": round(price_change, 2),
            "price_change_pct": round(price_change_pct, 2),
            "consolidation_range": consolidation,
            "breakout_analysis": breakout,
            "false_breakout_check": false_breakout,
            "signal": signal_result,
            "insights": insights,
            "atr_info": {
                "atr_14": round(atr, 2) if atr > 0 else None,
                "atr_percent": round((atr / float(current['Close'])) * 100, 2) if atr > 0 and float(current['Close']) > 0 else None,
            },
            "parameters": {
                "lookback_days": lookback,
                "volume_threshold": volume_threshold,
                "period": period,
            }
        }
        
    except YahooFinanceError as e:
        raise
    except Exception as e:
        raise YahooFinanceError(f"Error analyzing breakout for {ticker}: {str(e)}")

