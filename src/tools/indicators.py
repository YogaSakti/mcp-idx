"""Tool for getting technical indicators."""

from typing import Any, Dict, List
import pandas as pd
import pandas_ta as ta
from mcp.types import Tool
from src.utils.yahoo import yahoo_client, YahooFinanceError
from src.utils.validators import validate_ticker, validate_period, validate_indicators
from src.config.settings import settings
# format_ticker handled by yahoo_client internally


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
                    "description": "List indikator (rsi, macd, sma_20, ema_50, bbands, stoch, atr, obv, vwap, adx, ichimoku)",
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
                    # NaN guard: RSI butuh minimal 14 bars
                    if pd.notna(rsi_value):
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
                    # NaN guard: MACD butuh cukup data untuk EMA 12, 26, dan signal 9
                    if macd_line is not None and signal_line is not None and pd.notna(macd_line) and pd.notna(signal_line):
                        interpretation = (
                            "bullish" if macd_line > signal_line else "bearish"
                        )
                        result["macd"] = {
                            "macd_line": round(float(macd_line), 2),
                            "signal_line": round(float(signal_line), 2),
                            "histogram": round(float(histogram), 2) if histogram is not None and pd.notna(histogram) else None,
                            "interpretation": interpretation,
                        }

            elif ind.startswith("sma_"):
                period = int(ind.split("_")[1])
                sma = ta.sma(close, length=period)
                if not sma.empty:
                    sma_value = sma.iloc[-1]
                    # NaN guard: skip jika data tidak cukup untuk period ini
                    if pd.notna(sma_value):
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
                    # NaN guard: skip jika data tidak cukup untuk period ini
                    if pd.notna(ema_value):
                        current_price = close.iloc[-1]
                        result[ind] = {
                            "value": round(float(ema_value), 2),
                            "price_vs_ema": "above" if current_price > ema_value else "below",
                        }

            elif ind == "bbands":
                bbands = ta.bbands(close, length=20, std=2)
                if bbands is not None and not bbands.empty:
                    # Use column names instead of hardcoded indices (more robust)
                    # pandas_ta returns: BBL_20_2.0, BBM_20_2.0, BBU_20_2.0, BBB_20_2.0, BBP_20_2.0
                    bb_cols = bbands.columns.tolist()
                    upper_col = [c for c in bb_cols if 'BBU' in c][0] if any('BBU' in c for c in bb_cols) else bb_cols[2]
                    middle_col = [c for c in bb_cols if 'BBM' in c][0] if any('BBM' in c for c in bb_cols) else bb_cols[1]
                    lower_col = [c for c in bb_cols if 'BBL' in c][0] if any('BBL' in c for c in bb_cols) else bb_cols[0]
                    
                    current_price_bb = close.iloc[-1]
                    upper_val = float(bbands[upper_col].iloc[-1])
                    middle_val = float(bbands[middle_col].iloc[-1])
                    lower_val = float(bbands[lower_col].iloc[-1])
                    
                    # Position dalam band (untuk IDX, penting untuk timing)
                    bb_width = upper_val - lower_val
                    bb_position = ((current_price_bb - lower_val) / bb_width * 100) if bb_width > 0 else 50
                    
                    result["bbands"] = {
                        "upper": round(upper_val, 2),
                        "middle": round(middle_val, 2),
                        "lower": round(lower_val, 2),
                        "width": round(bb_width, 2),
                        "position_pct": round(bb_position, 1),  # 0=lower, 50=middle, 100=upper
                        "interpretation": "overbought" if bb_position > 80 else "oversold" if bb_position < 20 else "neutral"
                    }

            elif ind == "stoch":
                stoch = ta.stoch(high, low, close, k=14, d=3)
                if stoch is not None and not stoch.empty:
                    stoch_k = stoch.iloc[-1, 0]
                    stoch_d = stoch.iloc[-1, 1]
                    # NaN guard
                    if pd.notna(stoch_k) and pd.notna(stoch_d):
                        result["stoch"] = {
                            "k": round(float(stoch_k), 2),
                            "d": round(float(stoch_d), 2),
                        }

            elif ind == "atr":
                atr = ta.atr(high, low, close, length=14)
                if not atr.empty:
                    atr_value = atr.iloc[-1]
                    # NaN guard
                    if pd.notna(atr_value):
                        result["atr"] = {
                            "value": round(float(atr_value), 2),
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

                    # NaN guard: pastikan semua nilai valid
                    if (adx_value is not None and plus_di is not None and minus_di is not None and
                        pd.notna(adx_value) and pd.notna(plus_di) and pd.notna(minus_di)):
                        
                        # CRITICAL FIX: Clamp values to valid 0-100 range
                        # ADX, +DI, -DI should theoretically be 0-100
                        # Values >100 indicate calculation issues with pandas_ta
                        adx_value = min(max(float(adx_value), 0), 100)
                        plus_di = min(max(float(plus_di), 0), 100)
                        minus_di = min(max(float(minus_di), 0), 100)
                        
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
                            "value": round(adx_value, 2),
                            "plus_di": round(plus_di, 2),
                            "minus_di": round(minus_di, 2),
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
                        
                        # CRITICAL FIX: Check for NaN values before proceeding
                        # Ichimoku requires 52 bars minimum for complete calculation
                        # Senkou Span B especially needs 52 bars and is often NaN
                        tenkan_valid = pd.notna(tenkan)
                        kijun_valid = pd.notna(kijun)
                        senkou_a_valid = pd.notna(senkou_a)
                        senkou_b_valid = pd.notna(senkou_b)
                        
                        # At minimum need tenkan and kijun for TK cross analysis
                        if tenkan_valid and kijun_valid:
                            # TK Cross (Tenkan-Kijun crossover) - always available if tenkan/kijun valid
                            tk_cross = "bullish" if tenkan > kijun else "bearish"
                            
                            # Cloud analysis - only if both spans available
                            if senkou_a_valid and senkou_b_valid:
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
                                    
                                # Overall signal (full analysis)
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
                            else:
                                # Partial data - only TK cross available, use price vs kijun for cloud substitute
                                cloud_color = "unknown"
                                price_vs_cloud = "above" if current_price > kijun else "below" if current_price < kijun else "at"
                                signal = "bullish" if tk_cross == "bullish" and price_vs_cloud == "above" else \
                                         "bearish" if tk_cross == "bearish" and price_vs_cloud == "below" else "neutral"

                            result["ichimoku"] = {
                                "tenkan_sen": round(float(tenkan), 2),
                                "kijun_sen": round(float(kijun), 2),
                                "senkou_span_a": round(float(senkou_a), 2) if senkou_a_valid else None,
                                "senkou_span_b": round(float(senkou_b), 2) if senkou_b_valid else None,
                                "cloud_color": cloud_color,
                                "price_vs_cloud": price_vs_cloud,
                                "tk_cross": tk_cross,
                                "signal": signal,
                                "data_complete": senkou_a_valid and senkou_b_valid,
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
    ADAPTED FOR IDX MARKET - Di pasar Indonesia, momentum bisa extended.

    Args:
        indicators: Dictionary of calculated indicators
        current_price: Current stock price

    Returns:
        Overall signal: "bullish", "bearish", or "neutral"
    """
    bullish_signals = 0
    bearish_signals = 0
    warnings = []

    # Check RSI - Di IDX, RSI adalah WARNING bukan direct signal
    # Saham bandar bisa overbought berhari-hari, oversold juga bisa turun terus
    if "rsi_14" in indicators:
        rsi_value = indicators["rsi_14"].get("value")
        # NaN guard: pastikan value valid
        if rsi_value is not None and pd.notna(rsi_value):
            # RSI sebagai FILTER, bukan signal generator
            if rsi_value < 30:
                # Oversold = POTENTIAL reversal, tapi bisa jadi falling knife
                # Jangan langsung bullish, cek konfirmasi lain
                warnings.append("oversold")
            elif rsi_value > 80:  # Extreme overbought (dinaikkan dari 70)
                # Di IDX, RSI 70-80 masih bisa lanjut naik
                # Baru warning di >80
                warnings.append("extreme_overbought")
            elif rsi_value > 70:
                # Overbought tapi di IDX ini masih bisa momentum
                # Tidak langsung bearish
                pass

    # Check MACD - Lebih reliable di IDX
    if "macd" in indicators:
        macd_interp = indicators["macd"].get("interpretation")
        if macd_interp:  # NaN guard
            if macd_interp == "bullish":
                bullish_signals += 1.5  # Higher weight untuk MACD
            else:
                bearish_signals += 1.5

    # Check ADX untuk trend strength (penting di IDX)
    if "adx" in indicators:
        adx_data = indicators["adx"]
        adx_value = adx_data.get("value")
        # NaN guard: pastikan ADX value valid
        if adx_value is not None and pd.notna(adx_value):
            if adx_data.get("trend_strength") == "strong":
                # Strong trend - follow the direction
                if adx_data.get("trend_direction") == "bullish":
                    bullish_signals += 2  # High weight for strong bullish trend
                else:
                    bearish_signals += 2
            elif adx_data.get("trend_strength") == "developing":
                if adx_data.get("trend_direction") == "bullish":
                    bullish_signals += 1
                else:
                    bearish_signals += 1

    # Check SMA/EMA - Price position vs MA (DYNAMIC - berdasarkan MA yang tersedia)
    ma_above_count = 0
    ma_below_count = 0
    ma_total_available = 0
    
    # Cari semua MA yang ada di indicators (tidak hardcode list)
    for key, value in indicators.items():
        if key.startswith("sma_") or key.startswith("ema_"):
            # NaN guard: cek apakah MA value valid
            ma_value = value.get("value")
            if ma_value is not None and pd.notna(ma_value):
                ma_total_available += 1
                position = value.get("price_vs_sma") or value.get("price_vs_ema")
                if position == "above":
                    ma_above_count += 1
                elif position == "below":
                    ma_below_count += 1
    
    # Dynamic MA alignment scoring berdasarkan MA yang tersedia
    if ma_total_available > 0:
        alignment_ratio = ma_above_count / ma_total_available
        
        if alignment_ratio == 1.0:  # Semua MA bullish
            bullish_signals += 2
        elif alignment_ratio >= 0.67:  # Mayoritas bullish
            bullish_signals += 1
        elif alignment_ratio == 0:  # Semua MA bearish
            bearish_signals += 2
        elif alignment_ratio <= 0.33:  # Mayoritas bearish
            bearish_signals += 1
        # 0.34-0.66 = mixed, no bonus

    # Determine signal with IDX-specific logic
    if bullish_signals > bearish_signals + 1:  # Need clear margin
        if "extreme_overbought" in warnings:
            return "bullish_but_overbought"  # Bullish tapi hati-hati
        return "bullish"
    elif bearish_signals > bullish_signals + 1:
        if "oversold" in warnings:
            return "bearish_but_oversold"  # Bearish tapi mungkin bounce
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
        
        # CRITICAL: Sort by date ascending untuk memastikan indikator dihitung dengan benar
        # Beberapa API return data descending (terbaru dulu), yang akan bikin EMA/MACD/RSI salah
        df.sort_index(inplace=True)

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

