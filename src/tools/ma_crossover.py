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
            "untuk Indonesian stocks. Returns recent crossovers dalam 30 hari terakhir."
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

        # Calculate moving averages
        sma_50 = ta.sma(close, length=50)
        sma_200 = ta.sma(close, length=200)
        ema_12 = ta.ema(close, length=12)
        ema_26 = ta.ema(close, length=26)

        result = {
            "ticker": ticker,
            "period": period,
            "lookback_days": lookback_days,
            "current_price": round(float(close.iloc[-1]), 2),
            "crossovers": {},
        }

        # Detect Golden/Death Cross (SMA 50 x SMA 200)
        golden_death_cross = detect_crossover(sma_50, sma_200, dates, lookback_days)
        if golden_death_cross:
            result["crossovers"]["sma_50_200"] = golden_death_cross

        # Detect EMA 12 x EMA 26 crossovers
        ema_crossovers = detect_crossover(ema_12, ema_26, dates, lookback_days)
        if ema_crossovers:
            result["crossovers"]["ema_12_26"] = ema_crossovers

        # Current MA positions
        current_mas = {}
        if not pd.isna(sma_50.iloc[-1]):
            current_mas["sma_50"] = round(float(sma_50.iloc[-1]), 2)
        if not pd.isna(sma_200.iloc[-1]):
            current_mas["sma_200"] = round(float(sma_200.iloc[-1]), 2)
        if not pd.isna(ema_12.iloc[-1]):
            current_mas["ema_12"] = round(float(ema_12.iloc[-1]), 2)
        if not pd.isna(ema_26.iloc[-1]):
            current_mas["ema_26"] = round(float(ema_26.iloc[-1]), 2)

        result["current_mas"] = current_mas

        # Current alignment (bullish if fast > slow)
        alignments = {}
        if "sma_50" in current_mas and "sma_200" in current_mas:
            alignments["sma_50_200"] = "bullish" if current_mas["sma_50"] > current_mas["sma_200"] else "bearish"
        if "ema_12" in current_mas and "ema_26" in current_mas:
            alignments["ema_12_26"] = "bullish" if current_mas["ema_12"] > current_mas["ema_26"] else "bearish"

        result["current_alignment"] = alignments

        # Trading insights
        insights = []
        if golden_death_cross:
            latest = golden_death_cross[-1]
            if latest["signal"] == "bullish":
                insights.append(f"✅ Golden Cross detected on {latest['date']} - Long-term bullish signal")
            else:
                insights.append(f"⚠️ Death Cross detected on {latest['date']} - Long-term bearish signal")

        if ema_crossovers:
            latest = ema_crossovers[-1]
            if latest["signal"] == "bullish":
                insights.append(f"📈 EMA bullish crossover on {latest['date']} - Short-term bullish momentum")
            else:
                insights.append(f"📉 EMA bearish crossover on {latest['date']} - Short-term bearish momentum")

        if not golden_death_cross and not ema_crossovers:
            insights.append("No crossovers detected in the lookback period")

        result["insights"] = insights

        return result

    except Exception as e:
        return {
            "ticker": ticker,
            "error": str(e),
        }
