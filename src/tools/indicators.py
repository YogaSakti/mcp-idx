"""Tool for getting technical indicators."""

from typing import Any, Dict, List
import pandas as pd
import pandas_ta as ta
from mcp.types import Tool
from src.utils.yahoo import yahoo_client, YahooFinanceError
from src.utils.validators import validate_ticker, validate_period, validate_indicators
from src.config.settings import settings
from src.utils.helpers import format_ticker


def get_technical_indicators_tool() -> Tool:
    """Get technical indicators tool definition."""
    return Tool(
        name="get_technical_indicators",
        description="Menghitung indikator teknikal untuk analisis saham IDX.",
        inputSchema={
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Ticker saham IDX (contoh: TLKM, BBCA, BBRI)",
                },
                "indicators": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List indikator (rsi, macd, sma_20, ema_50, bbands, stoch, atr, obv, vwap, adx)",
                    "default": settings.DEFAULT_INDICATORS,
                },
                "period": {
                    "type": "string",
                    "description": "Periode data untuk kalkulasi (1mo, 3mo, 6mo, 1y)",
                    "default": "3mo",
                },
            },
            "required": ["ticker"],
        },
    )


def calculate_indicators(df: pd.DataFrame, indicators: List[str]) -> Dict[str, Any]:
    """
    Calculate technical indicators from DataFrame.

    Args:
        df: DataFrame with OHLCV data
        indicators: List of indicator names to calculate

    Returns:
        Dictionary with calculated indicators
    """
    result = {}
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    for ind in indicators:
        try:
            if ind in ["rsi", "rsi_14"]:
                rsi = ta.rsi(close, length=14)
                if not rsi.empty:
                    rsi_value = rsi.iloc[-1]
                    interpretation = (
                        "overbought" if rsi_value > 70
                        else "oversold" if rsi_value < 30
                        else "neutral"
                    )
                    result["rsi_14"] = {
                        "value": round(float(rsi_value), 2),
                        "interpretation": interpretation,
                    }

            elif ind == "macd":
                macd_data = ta.macd(close)
                if macd_data is not None and not macd_data.empty:
                    macd_line = macd_data.iloc[-1, 0] if len(macd_data.columns) > 0 else None
                    signal_line = macd_data.iloc[-1, 1] if len(macd_data.columns) > 1 else None
                    histogram = macd_data.iloc[-1, 2] if len(macd_data.columns) > 2 else None
                    if macd_line is not None and signal_line is not None:
                        interpretation = (
                            "bullish" if macd_line > signal_line else "bearish"
                        )
                        result["macd"] = {
                            "macd_line": round(float(macd_line), 2),
                            "signal_line": round(float(signal_line), 2),
                            "histogram": round(float(histogram), 2) if histogram is not None else None,
                            "interpretation": interpretation,
                        }

            elif ind.startswith("sma_"):
                period = int(ind.split("_")[1])
                sma = ta.sma(close, length=period)
                if not sma.empty:
                    sma_value = sma.iloc[-1]
                    current_price = close.iloc[-1]
                    result[ind] = {
                        "value": round(float(sma_value), 2),
                        "price_vs_sma": "above" if current_price > sma_value else "below",
                    }

            elif ind.startswith("ema_"):
                period = int(ind.split("_")[1])
                ema = ta.ema(close, length=period)
                if not ema.empty:
                    ema_value = ema.iloc[-1]
                    current_price = close.iloc[-1]
                    result[ind] = {
                        "value": round(float(ema_value), 2),
                        "price_vs_ema": "above" if current_price > ema_value else "below",
                    }

            elif ind == "bbands":
                bbands = ta.bbands(close, length=20, std=2)
                if bbands is not None and not bbands.empty:
                    result["bbands"] = {
                        "upper": round(float(bbands.iloc[-1, 0]), 2),
                        "middle": round(float(bbands.iloc[-1, 1]), 2),
                        "lower": round(float(bbands.iloc[-1, 2]), 2),
                    }

            elif ind == "stoch":
                stoch = ta.stoch(high, low, close, k=14, d=3)
                if stoch is not None and not stoch.empty:
                    result["stoch"] = {
                        "k": round(float(stoch.iloc[-1, 0]), 2),
                        "d": round(float(stoch.iloc[-1, 1]), 2),
                    }

            elif ind == "atr":
                atr = ta.atr(high, low, close, length=14)
                if not atr.empty:
                    result["atr"] = {
                        "value": round(float(atr.iloc[-1]), 2),
                    }

            elif ind == "obv":
                obv = ta.obv(close, volume)
                if not obv.empty:
                    result["obv"] = {
                        "value": round(float(obv.iloc[-1]), 2),
                    }

            elif ind == "vwap":
                vwap = ta.vwap(high, low, close, volume)
                if not vwap.empty:
                    result["vwap"] = {
                        "value": round(float(vwap.iloc[-1]), 2),
                    }

            elif ind == "adx":
                # Calculate ADX with pandas_ta
                adx_data = ta.adx(high, low, close, length=14)
                if adx_data is not None and not adx_data.empty:
                    # pandas_ta returns DataFrame with columns: ADX_14, DMP_14, DMN_14
                    adx_value = adx_data['ADX_14'].iloc[-1] if 'ADX_14' in adx_data.columns else None
                    plus_di = adx_data['DMP_14'].iloc[-1] if 'DMP_14' in adx_data.columns else None
                    minus_di = adx_data['DMN_14'].iloc[-1] if 'DMN_14' in adx_data.columns else None

                    if adx_value is not None and plus_di is not None and minus_di is not None:
                        # Interpret trend strength based on ADX value
                        if adx_value > 25:
                            trend_strength = "strong"
                        elif adx_value >= 20:
                            trend_strength = "developing"
                        else:
                            trend_strength = "weak"

                        # Interpret trend direction based on DI comparison
                        trend_direction = "bullish" if plus_di > minus_di else "bearish"

                        result["adx"] = {
                            "value": round(float(adx_value), 2),
                            "plus_di": round(float(plus_di), 2),
                            "minus_di": round(float(minus_di), 2),
                            "trend_strength": trend_strength,
                            "trend_direction": trend_direction,
                        }

            elif ind == "ichimoku":
                # Calculate Ichimoku Cloud (lookahead=False to avoid data leak)
                ichimoku_result = ta.ichimoku(high, low, close, lookahead=False)

                if ichimoku_result is not None and len(ichimoku_result) == 2:
                    hist_df = ichimoku_result[0]  # Historical DataFrame

                    if not hist_df.empty and len(hist_df) > 0:
                        # Get latest values
                        tenkan = hist_df['ITS_9'].iloc[-1]  # Tenkan-sen (Conversion Line)
                        kijun = hist_df['IKS_26'].iloc[-1]  # Kijun-sen (Base Line)
                        senkou_a = hist_df['ISA_9'].iloc[-1]  # Senkou Span A (Leading Span A)
                        senkou_b = hist_df['ISB_26'].iloc[-1]  # Senkou Span B (Leading Span B)

                        current_price = close.iloc[-1]

                        # Cloud interpretation
                        cloud_color = "bullish" if senkou_a > senkou_b else "bearish"
                        cloud_top = max(senkou_a, senkou_b)
                        cloud_bottom = min(senkou_a, senkou_b)

                        # Price vs Cloud position
                        if current_price > cloud_top:
                            price_vs_cloud = "above"
                        elif current_price < cloud_bottom:
                            price_vs_cloud = "below"
                        else:
                            price_vs_cloud = "inside"

                        # TK Cross (Tenkan-Kijun crossover)
                        tk_cross = "bullish" if tenkan > kijun else "bearish"

                        # Overall signal
                        if tenkan > kijun and price_vs_cloud == "above" and cloud_color == "bullish":
                            signal = "strong_bullish"
                        elif tenkan < kijun and price_vs_cloud == "below" and cloud_color == "bearish":
                            signal = "strong_bearish"
                        elif price_vs_cloud == "above":
                            signal = "bullish"
                        elif price_vs_cloud == "below":
                            signal = "bearish"
                        else:
                            signal = "neutral"

                        result["ichimoku"] = {
                            "tenkan_sen": round(float(tenkan), 2),
                            "kijun_sen": round(float(kijun), 2),
                            "senkou_span_a": round(float(senkou_a), 2),
                            "senkou_span_b": round(float(senkou_b), 2),
                            "cloud_color": cloud_color,
                            "price_vs_cloud": price_vs_cloud,
                            "tk_cross": tk_cross,
                            "signal": signal,
                        }

        except Exception:
            # Skip indicators that fail to calculate
            continue

    return result


def calculate_support_resistance(df: pd.DataFrame) -> Dict[str, List[float]]:
    """
    Calculate support and resistance levels.

    Args:
        df: DataFrame with OHLCV data

    Returns:
        Dictionary with support and resistance levels
    """
    high = df["High"]
    low = df["Low"]
    close = df["Close"]

    # Simple support/resistance calculation based on recent highs and lows
    recent_highs = high.tail(20).nlargest(3).tolist()
    recent_lows = low.tail(20).nsmallest(3).tolist()

    # Remove duplicates and sort
    resistance_levels = sorted(set(recent_highs), reverse=True)[:3]
    support_levels = sorted(set(recent_lows))[:3]

    return {
        "support_levels": [round(float(level), 2) for level in support_levels],
        "resistance_levels": [round(float(level), 2) for level in resistance_levels],
    }


def determine_overall_signal(indicators: Dict[str, Any], current_price: float) -> str:
    """
    Determine overall signal from indicators.

    Args:
        indicators: Dictionary of calculated indicators
        current_price: Current stock price

    Returns:
        Overall signal: "bullish", "bearish", or "neutral"
    """
    bullish_signals = 0
    bearish_signals = 0

    # Check RSI
    if "rsi_14" in indicators:
        rsi_value = indicators["rsi_14"]["value"]
        if rsi_value < 30:
            bullish_signals += 1
        elif rsi_value > 70:
            bearish_signals += 1

    # Check MACD
    if "macd" in indicators:
        if indicators["macd"]["interpretation"] == "bullish":
            bullish_signals += 1
        else:
            bearish_signals += 1

    # Check SMA/EMA
    for key in ["sma_20", "sma_50", "ema_50"]:
        if key in indicators:
            if indicators[key].get("price_vs_sma") == "above" or indicators[key].get("price_vs_ema") == "above":
                bullish_signals += 1
            else:
                bearish_signals += 1

    if bullish_signals > bearish_signals:
        return "bullish"
    elif bearish_signals > bullish_signals:
        return "bearish"
    else:
        return "neutral"


async def get_technical_indicators(args: dict[str, Any]) -> dict[str, Any]:
    """
    Get technical indicators.

    Args:
        args: Dictionary with 'ticker', optional 'indicators' and 'period' keys

    Returns:
        Dictionary with technical indicators
    """
    try:
        ticker = validate_ticker(args.get("ticker", ""))
        period = validate_period(args.get("period", "3mo"))
        indicators = validate_indicators(args.get("indicators", settings.DEFAULT_INDICATORS))

        # Get historical data
        hist_data = yahoo_client.get_historical_data(ticker, period=period, interval="1d")
        if "error" in hist_data:
            return hist_data

        # Convert to DataFrame
        df_data = hist_data["data"]
        df = pd.DataFrame(df_data)
        df["Date"] = pd.to_datetime(df["date"])
        df.set_index("Date", inplace=True)

        # Rename columns to match pandas_ta expectations (capitalize first letter)
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

        # Calculate indicators
        calculated_indicators = calculate_indicators(df, indicators)

        # Calculate support/resistance
        support_resistance = calculate_support_resistance(df)

        # Determine overall signal
        overall_signal = determine_overall_signal(calculated_indicators, current_price)

        result = {
            "ticker": ticker,
            "period": period,
            "current_price": current_price,
            "indicators": calculated_indicators,
            "overall_signal": overall_signal,
            **support_resistance,
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
            "message": f"Gagal menghitung indikator: {str(e)}",
        }

