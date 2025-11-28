"""Tool for volatility analysis."""

from typing import Any, Dict, Optional
import pandas as pd
import numpy as np
import pandas_ta as ta
from mcp.types import Tool
from src.utils.yahoo import yahoo_client, YahooFinanceError
from src.utils.validators import validate_ticker
from src.utils.exceptions import InvalidParameterError, DataUnavailableError, NetworkError
from src.utils.cache import cache_manager


def get_volatility_analysis_tool() -> Tool:
    """Get volatility analysis tool definition."""
    return Tool(
        name="get_volatility_analysis",
        description="Menganalisis volatilitas saham IDX. Menghitung historical volatility, beta terhadap IHSG, ATR-based volatility, dan risk level.",
        inputSchema={
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Ticker saham IDX (contoh: BBCA, BBRI, TLKM)",
                },
                "period": {
                    "type": "string",
                    "description": "Periode analisis (30d, 90d, 1y, 2y) - default: 1y",
                    "default": "1y",
                },
            },
            "required": ["ticker"],
        },
    )


def calculate_historical_volatility(df: pd.DataFrame, periods: list[int] = [30, 90, 252]) -> Dict[str, Any]:
    """
    Calculate historical volatility for different periods.
    
    Args:
        df: DataFrame with close prices
        periods: List of periods in days
        
    Returns:
        Dictionary with volatility metrics
    """
    if df.empty or len(df) < 2:
        return {}
    
    closes = df["close"].values
    if len(closes) < 2:
        return {}
    
    # Calculate daily returns
    returns = pd.Series(closes).pct_change().dropna()
    
    if len(returns) < 2:
        return {}
    
    volatilities = {}
    
    for period in periods:
        if len(returns) >= period:
            period_returns = returns[-period:]
            # Annualized volatility (assuming 252 trading days per year)
            vol = period_returns.std() * np.sqrt(252) * 100
            volatilities[f"{period}d"] = round(vol, 2)
        elif len(returns) >= period // 2:
            # Use available data if at least half the period
            period_returns = returns
            vol = period_returns.std() * np.sqrt(252) * 100
            volatilities[f"{period}d"] = round(vol, 2)
    
    # Overall volatility
    overall_vol = returns.std() * np.sqrt(252) * 100
    volatilities["overall"] = round(overall_vol, 2)
    
    return volatilities


def calculate_beta(stock_returns: pd.Series, market_returns: pd.Series) -> Optional[float]:
    """
    Calculate beta coefficient.
    
    Args:
        stock_returns: Series of stock returns
        market_returns: Series of market returns
        
    Returns:
        Beta coefficient or None
    """
    # Align indices
    aligned = pd.DataFrame({
        "stock": stock_returns,
        "market": market_returns
    }).dropna()
    
    if len(aligned) < 30:  # Need at least 30 data points
        return None
    
    stock_ret = aligned["stock"].values
    market_ret = aligned["market"].values
    
    # Calculate covariance and variance
    covariance = np.cov(stock_ret, market_ret)[0][1]
    market_variance = np.var(market_ret)
    
    if market_variance == 0:
        return None
    
    beta = covariance / market_variance
    return round(float(beta), 3)


def calculate_atr_volatility(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate ATR-based volatility metrics.
    
    Args:
        df: DataFrame with OHLC data
        
    Returns:
        Dictionary with ATR metrics
    """
    if df.empty or len(df) < 14:
        return {}
    
    # Rename columns if needed
    if "High" not in df.columns:
        df = df.rename(columns={
            "high": "High",
            "low": "Low",
            "close": "Close"
        })
    
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    
    # Calculate ATR
    atr = ta.atr(high, low, close, length=14)
    
    if atr.empty:
        return {}
    
    current_atr = float(atr.iloc[-1])
    avg_atr = float(atr.mean())
    current_price = float(close.iloc[-1])
    
    # ATR as percentage of price
    atr_percent = (current_atr / current_price * 100) if current_price > 0 else 0
    avg_atr_percent = (avg_atr / current_price * 100) if current_price > 0 else 0
    
    return {
        "atr_14": round(current_atr, 2),
        "atr_avg": round(avg_atr, 2),
        "atr_percent": round(atr_percent, 2),
        "atr_avg_percent": round(avg_atr_percent, 2),
    }


def determine_risk_level(volatility: float, beta: Optional[float] = None) -> Dict[str, Any]:
    """
    Determine risk level based on volatility and beta.
    
    Args:
        volatility: Annualized volatility percentage
        beta: Beta coefficient (optional)
        
    Returns:
        Dictionary with risk assessment
    """
    # Volatility-based risk
    if volatility < 15:
        vol_risk = "low"
    elif volatility < 30:
        vol_risk = "moderate"
    elif volatility < 50:
        vol_risk = "high"
    else:
        vol_risk = "very_high"
    
    # Beta-based risk
    beta_risk = None
    if beta is not None:
        if beta < 0.7:
            beta_risk = "defensive"
        elif beta < 1.0:
            beta_risk = "low_volatility"
        elif beta <= 1.3:
            beta_risk = "market_like"
        elif beta <= 1.7:
            beta_risk = "aggressive"
        else:
            beta_risk = "very_aggressive"
    
    # Overall risk level
    risk_score = 0
    if vol_risk == "low":
        risk_score += 1
    elif vol_risk == "moderate":
        risk_score += 2
    elif vol_risk == "high":
        risk_score += 3
    else:
        risk_score += 4
    
    if beta_risk:
        if beta_risk in ["defensive", "low_volatility"]:
            risk_score += 0.5
        elif beta_risk in ["aggressive", "very_aggressive"]:
            risk_score += 1
    
    if risk_score <= 1.5:
        overall_risk = "low"
    elif risk_score <= 2.5:
        overall_risk = "moderate"
    elif risk_score <= 3.5:
        overall_risk = "high"
    else:
        overall_risk = "very_high"
    
    return {
        "volatility_risk": vol_risk,
        "beta_risk": beta_risk,
        "overall_risk": overall_risk,
        "risk_score": round(risk_score, 1),
    }


async def get_volatility_analysis(args: dict[str, Any]) -> dict[str, Any]:
    """
    Get comprehensive volatility analysis.
    
    Args:
        args: Dictionary with 'ticker' and optional 'period' key
        
    Returns:
        Dictionary with volatility analysis
    """
    try:
        ticker = validate_ticker(args.get("ticker", ""))
        period = args.get("period", "1y")
        
        # Validate period
        valid_periods = ["30d", "90d", "1y", "2y"]
        if period not in valid_periods:
            period = "1y"
        
        # Check cache
        cache_key = cache_manager.generate_key("volatility_analysis", ticker, period)
        cached = cache_manager.get("historical_daily", cache_key)
        if cached:
            return cached
        
        # Get stock historical data
        hist_data = yahoo_client.get_historical_data(ticker, period=period, interval="1d")
        if "error" in hist_data:
            raise DataUnavailableError(f"Tidak dapat mengambil data historical untuk {ticker}")
        
        if not hist_data.get("data") or len(hist_data["data"]) < 30:
            raise DataUnavailableError(f"Data historical tidak cukup untuk analisis volatilitas {ticker}")
        
        # Convert to DataFrame
        df_data = hist_data["data"]
        df = pd.DataFrame(df_data)
        df["Date"] = pd.to_datetime(df["date"])
        df.set_index("Date", inplace=True)
        
        # Ensure close column is numeric
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df = df[df["close"] > 0]
        
        if df.empty or len(df) < 30:
            raise DataUnavailableError(f"Data tidak valid untuk analisis volatilitas {ticker}")
        
        # Calculate historical volatility
        hist_vol = calculate_historical_volatility(df, periods=[30, 90, 252])
        
        # Calculate ATR-based volatility
        atr_vol = calculate_atr_volatility(df)
        
        # Calculate beta vs IHSG
        beta = None
        beta_period = period if period in ["1y", "2y"] else "1y"
        
        try:
            # Get IHSG data
            ihsg_data = yahoo_client.get_historical_data("^JKSE", period=beta_period, interval="1d")
            if not ihsg_data.get("error") and ihsg_data.get("data"):
                ihsg_df = pd.DataFrame(ihsg_data["data"])
                ihsg_df["Date"] = pd.to_datetime(ihsg_df["date"])
                ihsg_df.set_index("Date", inplace=True)
                ihsg_df["close"] = pd.to_numeric(ihsg_df["close"], errors="coerce")
                ihsg_df = ihsg_df[ihsg_df["close"] > 0]
                
                if not ihsg_df.empty and len(ihsg_df) >= 30:
                    # Calculate returns
                    stock_returns = pd.Series(df["close"].values).pct_change().dropna()
                    market_returns = pd.Series(ihsg_df["close"].values).pct_change().dropna()
                    
                    # Align dates
                    stock_returns.index = df.index[1:]
                    market_returns.index = ihsg_df.index[1:]
                    
                    # Calculate beta
                    beta = calculate_beta(stock_returns, market_returns)
        except Exception:
            # Beta calculation failed, continue without it
            beta = None
        
        # Get current price
        price_data = yahoo_client.get_current_price(ticker)
        current_price = price_data.get("price", 0)
        
        # Determine risk level
        main_vol = hist_vol.get("overall", hist_vol.get("1y", hist_vol.get("90d", 0)))
        risk_assessment = determine_risk_level(main_vol, beta)
        
        # Prepare result
        result = {
            "ticker": ticker,
            "name": price_data.get("name", ""),
            "current_price": round(current_price, 2),
            "period": period,
            "data_points": len(df),
            "historical_volatility": hist_vol,
            "atr_volatility": atr_vol,
            "beta": {
                "value": beta,
                "benchmark": "IHSG (^JKSE)",
                "interpretation": (
                    "defensive" if beta and beta < 0.7
                    else "low_volatility" if beta and beta < 1.0
                    else "market_like" if beta and 1.0 <= beta <= 1.3
                    else "aggressive" if beta and beta > 1.3
                    else None
                ),
            } if beta is not None else None,
            "risk_assessment": risk_assessment,
            "summary": {
                "volatility_level": hist_vol.get("overall", hist_vol.get("1y", "N/A")),
                "beta_level": beta if beta else "N/A",
                "risk_level": risk_assessment.get("overall_risk", "unknown"),
            },
        }
        
        # Cache result
        cache_manager.set("historical_daily", cache_key, result)
        
        return result
        
    except ValueError as e:
        raise InvalidParameterError(str(e))
    except YahooFinanceError as e:
        raise DataUnavailableError(str(e))
    except Exception as e:
        raise NetworkError(f"Gagal melakukan analisis volatilitas: {str(e)}")


