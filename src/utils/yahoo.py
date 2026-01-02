"""Yahoo Finance wrapper for IDX stock data."""

from typing import Optional, Dict, Any, List
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz
from src.config.settings import settings
from src.utils.helpers import format_ticker, normalize_ticker
from src.utils.cache import cache_manager


class YahooFinanceError(Exception):
    """Custom exception for Yahoo Finance errors."""

    pass


class YahooFinanceClient:
    """Yahoo Finance API client wrapper."""

    def __init__(self):
        """Initialize Yahoo Finance client."""
        self.timeout = settings.YAHOO_TIMEOUT
        self.jakarta_tz = pytz.timezone(settings.MARKET_TIMEZONE)

    def get_ticker(self, ticker: str):
        """
        Get yfinance Ticker object.

        Args:
            ticker: Stock ticker symbol

        Returns:
            yfinance Ticker object
        """
        formatted_ticker = format_ticker(ticker)
        return yf.Ticker(formatted_ticker, session=None)

    def _sanitize_ratio(self, value, max_val: float = 100) -> Optional[float]:
        """
        Sanitize financial ratios to catch Yahoo Finance data errors.
        
        Some IDX stocks return wildly incorrect P/B, P/S ratios (e.g., 11878)
        due to unit/currency scaling issues in Yahoo's data.
        
        Args:
            value: Raw ratio value
            max_val: Maximum reasonable value (default 100)
            
        Returns:
            Sanitized value or None if invalid
        """
        if value is None or value == 0:
            return None
        
        try:
            ratio = round(float(value), 2)
            # Catch obviously wrong values
            if ratio < 0 or ratio > max_val:
                return None  # Return None for impossible values
            return ratio
        except (TypeError, ValueError):
            return None
    
    def _sanitize_percentage(self, value, is_decimal: bool = True, max_val: float = 100) -> Optional[float]:
        """
        Sanitize percentage values (like dividend yield, profit margin).
        
        Yahoo Finance sometimes returns these as decimals (0.05 = 5%)
        and sometimes as already-percentages. Also catches impossible values.
        
        Args:
            value: Raw value
            is_decimal: If True, multiply by 100 to convert to percentage
            max_val: Maximum reasonable percentage
            
        Returns:
            Sanitized percentage or None if invalid
        """
        if value is None or value == 0:
            return None
        
        try:
            pct = float(value)
            if is_decimal:
                pct = pct * 100
            pct = round(pct, 2)
            
            # Catch obviously wrong values
            if pct < 0 or pct > max_val:
                return None  # Return None for impossible values
            return pct
        except (TypeError, ValueError):
            return None

    def get_current_price(self, ticker: str) -> Dict[str, Any]:
        """
        Get current stock price and basic info.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with price data

        Raises:
            YahooFinanceError: If data cannot be retrieved
        """
        cache_key = cache_manager.generate_key("price", ticker)
        cached = cache_manager.get("price", cache_key)
        if cached:
            return cached

        try:
            ticker_obj = self.get_ticker(ticker)
            info = ticker_obj.info

            if not info or "regularMarketPrice" not in info:
                raise YahooFinanceError(f"No data available for ticker {ticker}")

            current_price = info.get("regularMarketPrice") or info.get("currentPrice")
            previous_close = info.get("previousClose", current_price)
            change = current_price - previous_close if current_price and previous_close else 0
            change_percent = (
                (change / previous_close * 100) if previous_close else 0
            )

            result = {
                "ticker": normalize_ticker(ticker),
                "name": info.get("longName") or info.get("shortName", ""),
                "price": round(current_price, 2) if current_price else None,
                "previous_close": round(previous_close, 2) if previous_close else None,
                "change": round(change, 2) if change else 0,
                "change_percent": round(change_percent, 2) if change_percent else 0,
                "open": round(info.get("regularMarketOpen", 0), 2) or None,
                "high": round(info.get("regularMarketDayHigh", 0), 2) or None,
                "low": round(info.get("regularMarketDayLow", 0), 2) or None,
                "volume": info.get("regularMarketVolume", 0) or None,
                "market_cap": info.get("marketCap") or None,
                "timestamp": datetime.now(self.jakarta_tz).isoformat(),
                "market_status": "open" if info.get("marketState") == "REGULAR" else "closed",
            }

            cache_manager.set("price", cache_key, result)
            return result

        except Exception as e:
            raise YahooFinanceError(f"Failed to get price for {ticker}: {str(e)}")

    def get_historical_data(
        self, ticker: str, period: str = "1mo", interval: str = "1d"
    ) -> Dict[str, Any]:
        """
        Get historical OHLCV data.

        Args:
            ticker: Stock ticker symbol
            period: Period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max)
            interval: Interval (1d, 1wk, 1mo)

        Returns:
            Dictionary with historical data

        Raises:
            YahooFinanceError: If data cannot be retrieved
        """
        cache_type = (
            "historical_intraday" if interval in ["1m", "5m", "15m", "30m", "1h"]
            else "historical_daily"
        )
        cache_key = cache_manager.generate_key("historical", ticker, period, interval)
        cached = cache_manager.get(cache_type, cache_key)
        if cached:
            return cached

        try:
            ticker_obj = self.get_ticker(ticker)
            hist = ticker_obj.history(period=period, interval=interval)

            if hist.empty:
                raise YahooFinanceError(f"No historical data available for {ticker}")

            data_points = []
            for date, row in hist.iterrows():
                data_points.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "open": round(float(row["Open"]), 2),
                    "high": round(float(row["High"]), 2),
                    "low": round(float(row["Low"]), 2),
                    "close": round(float(row["Close"]), 2),
                    "volume": int(row["Volume"]) if pd.notna(row["Volume"]) else 0,
                })

            result = {
                "ticker": normalize_ticker(ticker),
                "period": period,
                "interval": interval,
                "data_points": len(data_points),
                "data": data_points,
            }

            cache_manager.set(cache_type, cache_key, result)
            return result

        except Exception as e:
            raise YahooFinanceError(
                f"Failed to get historical data for {ticker}: {str(e)}"
            )

    def get_stock_info(self, ticker: str) -> Dict[str, Any]:
        """
        Get comprehensive stock information.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with stock info

        Raises:
            YahooFinanceError: If data cannot be retrieved
        """
        cache_key = cache_manager.generate_key("info", ticker)
        cached = cache_manager.get("info", cache_key)
        if cached:
            return cached

        try:
            ticker_obj = self.get_ticker(ticker)
            info = ticker_obj.info

            if not info:
                raise YahooFinanceError(f"No info available for ticker {ticker}")

            # Get historical data for 52-week high/low
            hist_1y = ticker_obj.history(period="1y")
            hist_50d = ticker_obj.history(period="50d")
            hist_200d = ticker_obj.history(period="200d")

            result = {
                "ticker": normalize_ticker(ticker),
                "name": info.get("longName") or info.get("shortName", ""),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "description": info.get("longBusinessSummary", ""),
                "market_cap": info.get("marketCap") or None,
                "enterprise_value": info.get("enterpriseValue") or None,
                "shares_outstanding": info.get("sharesOutstanding") or None,
                "financials": {
                    "pe_ratio": self._sanitize_ratio(info.get("trailingPE"), max_val=1000),
                    "pb_ratio": self._sanitize_ratio(info.get("priceToBook"), max_val=100),
                    "ps_ratio": self._sanitize_ratio(info.get("priceToSalesTrailing12Months"), max_val=100),
                    "eps": round(info.get("trailingEps", 0), 2) or None,
                    "revenue": info.get("totalRevenue") or None,
                    "net_income": info.get("netIncomeToCommon") or None,
                    "profit_margin": self._sanitize_percentage(info.get("profitMargins"), is_decimal=True, max_val=100),
                },
                "dividends": {
                    "dividend_yield": self._sanitize_percentage(info.get("dividendYield"), is_decimal=True, max_val=50),
                    "dividend_rate": round(info.get("dividendRate", 0), 2) or None,
                    "payout_ratio": self._sanitize_percentage(info.get("payoutRatio"), is_decimal=True, max_val=150),
                    "ex_dividend_date": (
                        datetime.fromtimestamp(info["exDividendDate"]).strftime("%Y-%m-%d")
                        if info.get("exDividendDate") else None
                    ),
                },
                "price_history": {
                    "52w_high": round(float(hist_1y["High"].max()), 2) if not hist_1y.empty else None,
                    "52w_low": round(float(hist_1y["Low"].min()), 2) if not hist_1y.empty else None,
                    "50d_avg": round(float(hist_50d["Close"].mean()), 2) if not hist_50d.empty else None,
                    "200d_avg": round(float(hist_200d["Close"].mean()), 2) if not hist_200d.empty else None,
                },
                "website": info.get("website", ""),
            }

            cache_manager.set("info", cache_key, result)
            return result

        except Exception as e:
            raise YahooFinanceError(f"Failed to get info for {ticker}: {str(e)}")

    def get_multiple_prices(self, tickers: List[str]) -> Dict[str, Any]:
        """
        Get prices for multiple tickers.

        Args:
            tickers: List of ticker symbols

        Returns:
            Dictionary with prices for all tickers
        """
        results = []
        for ticker in tickers:
            try:
                price_data = self.get_current_price(ticker)
                results.append({
                    "ticker": price_data["ticker"],
                    "name": price_data["name"],
                    "price": price_data["price"],
                    "change": price_data["change"],
                    "change_percent": price_data["change_percent"],
                    "volume": price_data["volume"],
                })
            except Exception:
                # Skip failed tickers
                continue

        return {
            "timestamp": datetime.now(self.jakarta_tz).isoformat(),
            "count": len(results),
            "stocks": results,
        }


# Global client instance
yahoo_client = YahooFinanceClient()

