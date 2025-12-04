"""Tool for volume analysis."""

from typing import Any, Dict
import pandas as pd
import numpy as np
from mcp.types import Tool
from src.utils.yahoo import yahoo_client, YahooFinanceError
from src.utils.validators import validate_ticker
from src.utils.exceptions import InvalidParameterError, DataUnavailableError, NetworkError
from src.utils.cache import cache_manager


def get_volume_analysis_tool() -> Tool:
    """Get volume analysis tool definition."""
    return Tool(
        name="get_volume_analysis",
        description="Menganalisis volume trading saham IDX. Menghitung average volume, volume spikes, volume trend, dan korelasi volume-harga.",
        inputSchema={
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Ticker saham IDX (contoh: BBCA, BBRI, TLKM)",
                },
                "period": {
                    "type": "string",
                    "description": "Periode analisis (7d, 30d, 90d, 1mo, 3mo, 6mo, 1y)",
                    "default": "30d",
                },
            },
            "required": ["ticker"],
        },
    )


def calculate_volume_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate volume metrics from DataFrame.
    
    Args:
        df: DataFrame with date, volume, and price columns
        
    Returns:
        Dictionary with volume metrics
    """
    if df.empty or len(df) < 2:
        return {}
    
    volumes = df["volume"].values
    closes = df["close"].values
    
    # Current and recent volumes
    current_volume = int(volumes[-1]) if len(volumes) > 0 else 0
    previous_volume = int(volumes[-2]) if len(volumes) > 1 else 0
    
    # Average volumes for different periods
    avg_7d = int(np.mean(volumes[-7:])) if len(volumes) >= 7 else int(np.mean(volumes)) if len(volumes) > 0 else 0
    avg_30d = int(np.mean(volumes[-30:])) if len(volumes) >= 30 else int(np.mean(volumes)) if len(volumes) > 0 else 0
    avg_90d = int(np.mean(volumes[-90:])) if len(volumes) >= 90 else int(np.mean(volumes)) if len(volumes) > 0 else 0
    avg_all = int(np.mean(volumes)) if len(volumes) > 0 else 0
    
    # Volume ratios
    volume_ratio_7d = round((current_volume / avg_7d) if avg_7d > 0 else 0, 2)
    volume_ratio_30d = round((current_volume / avg_30d) if avg_30d > 0 else 0, 2)
    volume_ratio_90d = round((current_volume / avg_90d) if avg_90d > 0 else 0, 2)
    
    # Volume spike detection
    is_spike_7d = volume_ratio_7d >= 2.0
    is_spike_30d = volume_ratio_30d >= 2.0
    is_spike_90d = volume_ratio_90d >= 2.0
    
    spike_severity = "none"
    if is_spike_7d or is_spike_30d or is_spike_90d:
        max_ratio = max(volume_ratio_7d, volume_ratio_30d, volume_ratio_90d)
        if max_ratio >= 5.0:
            spike_severity = "extreme"
        elif max_ratio >= 3.0:
            spike_severity = "high"
        else:
            spike_severity = "moderate"
    
    # Volume trend analysis
    if len(volumes) >= 7:
        recent_7d_avg = np.mean(volumes[-7:])
        previous_7d_avg = np.mean(volumes[-14:-7]) if len(volumes) >= 14 else recent_7d_avg
        trend_7d = "increasing" if recent_7d_avg > previous_7d_avg * 1.1 else "decreasing" if recent_7d_avg < previous_7d_avg * 0.9 else "stable"
    else:
        trend_7d = "insufficient_data"
    
    if len(volumes) >= 30:
        recent_30d_avg = np.mean(volumes[-30:])
        previous_30d_avg = np.mean(volumes[-60:-30]) if len(volumes) >= 60 else recent_30d_avg
        trend_30d = "increasing" if recent_30d_avg > previous_30d_avg * 1.1 else "decreasing" if recent_30d_avg < previous_30d_avg * 0.9 else "stable"
    else:
        trend_30d = "insufficient_data"
    
    # Volume-price correlation
    volume_price_corr = 0.0
    if len(volumes) >= 10 and len(closes) >= 10:
        # Calculate price changes
        price_changes = np.diff(closes) / np.maximum(closes[:-1], 0.01)  # Avoid div by zero properly
        volume_changes = np.diff(volumes) / np.maximum(volumes[:-1], 1)  # Use max instead of adding 1
        
        # Calculate correlation
        if len(price_changes) > 1 and len(volume_changes) > 1:
            valid_indices = ~(np.isnan(price_changes) | np.isnan(volume_changes) | np.isinf(price_changes) | np.isinf(volume_changes))
            if np.sum(valid_indices) >= 5:
                price_changes_clean = price_changes[valid_indices]
                volume_changes_clean = volume_changes[valid_indices]
                if len(price_changes_clean) > 1 and len(volume_changes_clean) > 1:
                    corr_matrix = np.corrcoef(price_changes_clean, volume_changes_clean)
                    volume_price_corr = round(float(corr_matrix[0, 1]), 3) if not np.isnan(corr_matrix[0, 1]) else 0.0
    
    # Volume interpretation
    correlation_interpretation = (
        "strong_positive" if volume_price_corr >= 0.7
        else "moderate_positive" if volume_price_corr >= 0.3
        else "weak_positive" if volume_price_corr > 0
        else "weak_negative" if volume_price_corr >= -0.3
        else "moderate_negative" if volume_price_corr >= -0.7
        else "strong_negative" if volume_price_corr < -0.7
        else "no_correlation"
    )
    
    # Volume statistics
    max_volume = int(np.max(volumes)) if len(volumes) > 0 else 0
    min_volume = int(np.min(volumes)) if len(volumes) > 0 else 0
    volume_std = int(np.std(volumes)) if len(volumes) > 0 else 0
    
    # Unusual volume detection
    z_score = (current_volume - avg_all) / (volume_std + 1) if volume_std > 0 else 0
    is_unusual = abs(z_score) >= 2.0
    unusual_type = "high" if z_score >= 2.0 else "low" if z_score <= -2.0 else "normal"
    
    return {
        "current_volume": current_volume,
        "previous_volume": previous_volume,
        "volume_change": current_volume - previous_volume if previous_volume > 0 else 0,
        "volume_change_percent": round(((current_volume - previous_volume) / previous_volume * 100) if previous_volume > 0 else 0, 2),
        "averages": {
            "7d": avg_7d,
            "30d": avg_30d,
            "90d": avg_90d,
            "all_time": avg_all,
        },
        "volume_ratios": {
            "vs_7d_avg": volume_ratio_7d,
            "vs_30d_avg": volume_ratio_30d,
            "vs_90d_avg": volume_ratio_90d,
        },
        "spike_detection": {
            "is_spike_7d": is_spike_7d,
            "is_spike_30d": is_spike_30d,
            "is_spike_90d": is_spike_90d,
            "severity": spike_severity,
        },
        "trend": {
            "7d": trend_7d,
            "30d": trend_30d,
        },
        "volume_price_correlation": {
            "correlation": volume_price_corr,
            "interpretation": correlation_interpretation,
        },
        "statistics": {
            "max_volume": max_volume,
            "min_volume": min_volume,
            "std_deviation": volume_std,
        },
        "unusual_volume": {
            "is_unusual": is_unusual,
            "type": unusual_type,
            "z_score": round(z_score, 2),
        },
    }


async def get_volume_analysis(args: dict[str, Any]) -> dict[str, Any]:
    """
    Get comprehensive volume analysis.
    
    Args:
        args: Dictionary with 'ticker' and optional 'period' key
        
    Returns:
        Dictionary with volume analysis
    """
    try:
        ticker = validate_ticker(args.get("ticker", ""))
        period = args.get("period", "30d")
        
        # Validate period
        valid_periods = ["7d", "30d", "90d", "1mo", "3mo", "6mo", "1y"]
        if period not in valid_periods:
            period = "30d"
        
        # Check cache
        cache_key = cache_manager.generate_key("volume_analysis", ticker, period)
        cached = cache_manager.get("historical_daily", cache_key)  # Use historical_daily cache
        if cached:
            return cached
        
        # Get historical data
        hist_data = yahoo_client.get_historical_data(ticker, period=period, interval="1d")
        if "error" in hist_data:
            raise DataUnavailableError(f"Tidak dapat mengambil data historical untuk {ticker}")
        
        if not hist_data.get("data") or len(hist_data["data"]) < 2:
            raise DataUnavailableError(f"Data historical tidak cukup untuk analisis volume {ticker}")
        
        # Convert to DataFrame
        df_data = hist_data["data"]
        df = pd.DataFrame(df_data)
        df["Date"] = pd.to_datetime(df["date"])
        df.set_index("Date", inplace=True)
        
        # Ensure volume column exists and is numeric
        if "volume" not in df.columns:
            raise DataUnavailableError(f"Data volume tidak tersedia untuk {ticker}")
        
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0)
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        
        # Remove rows with invalid data
        df = df[(df["volume"] >= 0) & (df["close"] > 0)]
        
        if df.empty or len(df) < 2:
            raise DataUnavailableError(f"Data tidak valid untuk analisis volume {ticker}")
        
        # Get current price
        price_data = yahoo_client.get_current_price(ticker)
        current_price = price_data.get("price", 0)
        
        # Calculate volume metrics
        volume_metrics = calculate_volume_metrics(df)
        
        # Prepare result
        result = {
            "ticker": ticker,
            "name": price_data.get("name", ""),
            "current_price": round(current_price, 2),
            "period": period,
            "data_points": len(df),
            **volume_metrics,
            "summary": {
                "current_volume_status": (
                    "spike" if volume_metrics.get("spike_detection", {}).get("severity") != "none"
                    else "above_average" if volume_metrics.get("volume_ratios", {}).get("vs_30d_avg", 0) > 1.2
                    else "below_average" if volume_metrics.get("volume_ratios", {}).get("vs_30d_avg", 0) < 0.8
                    else "normal"
                ),
                "trend": volume_metrics.get("trend", {}).get("30d", "unknown"),
                "correlation_strength": volume_metrics.get("volume_price_correlation", {}).get("interpretation", "unknown"),
            },
        }
        
        # Cache result (use historical_daily cache type)
        cache_manager.set("historical_daily", cache_key, result)
        
        return result
        
    except ValueError as e:
        raise InvalidParameterError(str(e))
    except YahooFinanceError as e:
        raise DataUnavailableError(str(e))
    except Exception as e:
        raise NetworkError(f"Gagal melakukan analisis volume: {str(e)}")


