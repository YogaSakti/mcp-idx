"""
Foreign Flow & Smart Money Analysis
Deteksi akumulasi/distribusi dari investor asing dan institusi
"""

from ..utils.yahoo import YahooFinanceClient
from ..utils.validators import validate_ticker
from mcp.types import Tool
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Initialize API
yahoo_api = YahooFinanceClient()


def analyze_foreign_flow(ticker: str, period: str = "1mo") -> dict:
    """
    Analisis aliran dana asing (foreign flow) dan institusi.
    
    Args:
        ticker: Stock ticker (e.g., 'BBRI', 'BBCA')
        period: Period untuk analisis volume pattern
        
    Returns:
        Dictionary dengan analisis foreign flow
    """
    ticker = validate_ticker(ticker)
    
    try:
        # Get stock object
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Get institutional holders data
        institutional = stock.institutional_holders
        major_holders = stock.major_holders
        
        # Get historical data untuk volume analysis
        hist_data = yahoo_api.get_historical_data(ticker, period=period)
        
        if 'error' in hist_data or 'data' not in hist_data:
            return {"error": "No historical data available"}
        
        # Convert to DataFrame
        hist = pd.DataFrame(hist_data['data'])
        
        if hist.empty:
            return {"error": "No historical data available"}
        
        # Ensure proper column names (capitalize)
        hist.columns = [col.capitalize() for col in hist.columns]
        
        # Calculate volume metrics
        avg_volume = hist['Volume'].mean()
        recent_volume = hist['Volume'].tail(5).mean()
        volume_trend = ((recent_volume - avg_volume) / avg_volume) * 100
        
        # Analyze price-volume correlation
        hist['Returns'] = hist['Close'].pct_change()
        hist['Volume_Change'] = hist['Volume'].pct_change()
        
        # Detect accumulation/distribution
        # Accumulation: Price up + Volume up
        # Distribution: Price down + Volume up
        accumulation_days = len(hist[(hist['Returns'] > 0) & (hist['Volume'] > avg_volume)])
        distribution_days = len(hist[(hist['Returns'] < 0) & (hist['Volume'] > avg_volume)])
        
        # Foreign ownership data
        insiders_pct = info.get('heldPercentInsiders', 0) * 100
        institutions_pct = info.get('heldPercentInstitutions', 0) * 100
        float_institutions_pct = info.get('institutionsFloatPercentHeld', 0) * 100
        institutions_count = info.get('institutionsCount', 0)
        
        # Analyze institutional changes
        foreign_flow_trend = "Unknown"
        if institutional is not None and not institutional.empty:
            latest_change = institutional['pctChange'].iloc[0] if 'pctChange' in institutional.columns else 0
            if latest_change > 0.05:
                foreign_flow_trend = "🟢 Strong Accumulation"
            elif latest_change > 0:
                foreign_flow_trend = "🟢 Accumulation"
            elif latest_change < -0.05:
                foreign_flow_trend = "🔴 Strong Distribution"
            elif latest_change < 0:
                foreign_flow_trend = "🔴 Distribution"
            else:
                foreign_flow_trend = "⚪ Neutral"
        
        # Calculate smart money confidence
        smart_money_score = 0
        
        # Factor 1: Institutional ownership (max 30 points)
        if institutions_pct > 40:
            smart_money_score += 30
        elif institutions_pct > 25:
            smart_money_score += 20
        elif institutions_pct > 10:
            smart_money_score += 10
        
        # Factor 2: Accumulation vs Distribution (max 30 points)
        if accumulation_days > distribution_days * 1.5:
            smart_money_score += 30
        elif accumulation_days > distribution_days:
            smart_money_score += 20
        elif accumulation_days * 1.5 < distribution_days:
            smart_money_score += 0
        else:
            smart_money_score += 10
        
        # Factor 3: Volume trend (max 20 points)
        if volume_trend > 50:
            smart_money_score += 20
        elif volume_trend > 20:
            smart_money_score += 15
        elif volume_trend > 0:
            smart_money_score += 10
        elif volume_trend > -20:
            smart_money_score += 5
        
        # Factor 4: Number of institutions (max 20 points)
        if institutions_count > 300:
            smart_money_score += 20
        elif institutions_count > 200:
            smart_money_score += 15
        elif institutions_count > 100:
            smart_money_score += 10
        elif institutions_count > 50:
            smart_money_score += 5
        
        # Determine rating
        if smart_money_score >= 80:
            rating = "🔥 VERY STRONG"
        elif smart_money_score >= 60:
            rating = "🟢 STRONG"
        elif smart_money_score >= 40:
            rating = "🟡 MODERATE"
        elif smart_money_score >= 20:
            rating = "🟠 WEAK"
        else:
            rating = "🔴 VERY WEAK"
        
        return {
            "ticker": ticker.replace('.JK', ''),
            "analysis_period": period,
            "foreign_ownership": {
                "insiders_percent": round(insiders_pct, 2),
                "institutions_percent": round(institutions_pct, 2),
                "float_institutions_percent": round(float_institutions_pct, 2),
                "institutions_count": int(institutions_count)
            },
            "flow_analysis": {
                "trend": foreign_flow_trend,
                "accumulation_days": accumulation_days,
                "distribution_days": distribution_days,
                "net_pattern": "ACCUMULATION" if accumulation_days > distribution_days else "DISTRIBUTION"
            },
            "volume_metrics": {
                "average_volume": int(avg_volume),
                "recent_volume": int(recent_volume),
                "volume_trend_pct": round(volume_trend, 2),
                "volume_status": "🔥 High" if volume_trend > 20 else "🟢 Normal" if volume_trend > -20 else "🔴 Low"
            },
            "smart_money": {
                "score": smart_money_score,
                "rating": rating,
                "confidence": "HIGH" if smart_money_score >= 60 else "MODERATE" if smart_money_score >= 40 else "LOW"
            },
            "interpretation": {
                "ownership_level": "High" if institutions_pct > 30 else "Moderate" if institutions_pct > 15 else "Low",
                "foreign_interest": "Strong" if institutions_count > 200 else "Moderate" if institutions_count > 100 else "Weak",
                "pattern": "Bullish" if accumulation_days > distribution_days * 1.2 else "Bearish" if distribution_days > accumulation_days * 1.2 else "Neutral"
            }
        }
        
    except Exception as e:
        return {"error": str(e)}


def analyze_bandarmology(ticker: str, period: str = "3mo") -> dict:
    """
    Analisis pola akumulasi/distribusi bandar berdasarkan price-volume action.
    
    Konsep Bandarmology:
    - Akumulasi: Harga sideways/turun tapi volume tinggi (bandar ngumpulin)
    - Markup: Harga naik volume tinggi (bandar pump)
    - Distribusi: Harga tinggi volume tinggi (bandar jual)
    - Markdown: Harga turun volume rendah (bandar kabur)
    
    Args:
        ticker: Stock ticker
        period: Analysis period
        
    Returns:
        Dictionary dengan analisis bandarmology
    """
    ticker = validate_ticker(ticker)
    
    try:
        hist_data = yahoo_api.get_historical_data(ticker, period=period)
        
        if 'error' in hist_data or 'data' not in hist_data:
            return {"error": "No historical data available"}
        
        # Convert to DataFrame
        hist = pd.DataFrame(hist_data['data'])
        
        if hist.empty or len(hist) < 20:
            return {"error": "Insufficient data for bandarmology analysis"}
        
        # Ensure proper column names
        hist.columns = [col.capitalize() for col in hist.columns]
        
        # Calculate indicators
        hist['Returns'] = hist['Close'].pct_change()
        hist['Volume_MA20'] = hist['Volume'].rolling(20).mean()
        hist['Volume_Ratio'] = hist['Volume'] / hist['Volume_MA20']
        hist['Price_MA20'] = hist['Close'].rolling(20).mean()
        hist['Price_Change'] = ((hist['Close'] - hist['Price_MA20']) / hist['Price_MA20']) * 100
        
        # Recent data (last 20 days)
        recent = hist.tail(20)
        
        # Detect phases
        high_volume_days = len(recent[recent['Volume_Ratio'] > 1.2])
        
        # Price trend
        price_trend = (recent['Close'].iloc[-1] - recent['Close'].iloc[0]) / recent['Close'].iloc[0] * 100
        
        # Volume trend
        volume_trend = (recent['Volume'].tail(5).mean() - recent['Volume'].head(5).mean()) / recent['Volume'].head(5).mean() * 100
        
        # Detect accumulation (price flat/down, volume high)
        accumulation_score = 0
        distribution_score = 0
        markup_score = 0
        markdown_score = 0
        
        for _, row in recent.iterrows():
            if row['Volume_Ratio'] > 1.2:  # High volume
                if -2 < row['Returns'] * 100 < 2:  # Price sideways
                    accumulation_score += 1
                elif row['Returns'] > 0.02:  # Price up
                    markup_score += 1
                elif row['Returns'] < -0.02:  # Price down (distribution or panic)
                    if row['Close'] > row['Price_MA20']:  # If price still high
                        distribution_score += 1
            else:  # Low volume
                if row['Returns'] < -0.01:  # Price down on low volume
                    markdown_score += 1
        
        # Determine current phase
        scores = {
            'ACCUMULATION': accumulation_score,
            'MARKUP': markup_score,
            'DISTRIBUTION': distribution_score,
            'MARKDOWN': markdown_score
        }
        
        current_phase = max(scores, key=scores.get)
        phase_strength = scores[current_phase]
        
        # Phase interpretation
        phase_signal = {
            'ACCUMULATION': '🟢 BUY - Bandar lagi ngumpulin',
            'MARKUP': '🔥 MOMENTUM - Bandar lagi pump',
            'DISTRIBUTION': '🔴 SELL - Bandar lagi jual',
            'MARKDOWN': '⚪ AVOID - Bandar udah kabur'
        }
        
        # Calculate bandar strength
        bandar_strength = (accumulation_score + markup_score) / len(recent) * 100
        
        return {
            "ticker": ticker.replace('.JK', ''),
            "analysis_period": period,
            "current_phase": {
                "phase": current_phase,
                "signal": phase_signal[current_phase],
                "strength": phase_strength,
                "confidence": "HIGH" if phase_strength >= 5 else "MODERATE" if phase_strength >= 3 else "LOW"
            },
            "phase_scores": {
                "accumulation": accumulation_score,
                "markup": markup_score,
                "distribution": distribution_score,
                "markdown": markdown_score
            },
            "price_action": {
                "trend_pct": round(price_trend, 2),
                "trend_direction": "UP" if price_trend > 5 else "DOWN" if price_trend < -5 else "SIDEWAYS",
                "current_price": round(hist['Close'].iloc[-1], 2),
                "ma20": round(hist['Price_MA20'].iloc[-1], 2),
                "position_vs_ma20": "ABOVE" if hist['Close'].iloc[-1] > hist['Price_MA20'].iloc[-1] else "BELOW"
            },
            "volume_action": {
                "high_volume_days": high_volume_days,
                "volume_trend_pct": round(volume_trend, 2),
                "volume_status": "INCREASING" if volume_trend > 20 else "DECREASING" if volume_trend < -20 else "STABLE"
            },
            "bandar_strength": {
                "score": round(bandar_strength, 2),
                "rating": "STRONG" if bandar_strength > 40 else "MODERATE" if bandar_strength > 20 else "WEAK",
                "active": bandar_strength > 30
            },
            "recommendation": {
                "action": "BUY" if current_phase in ['ACCUMULATION', 'MARKUP'] else "SELL" if current_phase == 'DISTRIBUTION' else "HOLD",
                "reason": phase_signal[current_phase],
                "risk_level": "LOW" if current_phase == 'ACCUMULATION' else "MODERATE" if current_phase == 'MARKUP' else "HIGH"
            }
        }
        
    except Exception as e:
        return {"error": str(e)}


def analyze_tape_reading(ticker: str, period: str = "5d") -> dict:
    """
    Analisis tape reading - membaca order flow dari price & volume action.
    
    Konsep:
    - Buying pressure: Price naik, volume tinggi, spread mengecil
    - Selling pressure: Price turun, volume tinggi, spread melebar
    - Absorption: Volume tinggi tapi price flat (ada yang nyerap)
    
    Args:
        ticker: Stock ticker
        period: Analysis period (5d untuk intraday reading)
        
    Returns:
        Dictionary dengan analisis tape reading
    """
    ticker = validate_ticker(ticker)
    
    try:
        hist_data = yahoo_api.get_historical_data(ticker, period=period, interval='1h')
        
        if 'error' in hist_data or 'data' not in hist_data:
            return {"error": "Insufficient intraday data"}
        
        # Convert to DataFrame
        hist = pd.DataFrame(hist_data['data'])
        
        if hist.empty or len(hist) < 10:
            return {"error": "Insufficient intraday data"}
        
        # Ensure proper column names
        hist.columns = [col.capitalize() for col in hist.columns]
        
        # Calculate metrics
        hist['Spread'] = ((hist['High'] - hist['Low']) / hist['Close']) * 100
        hist['Body'] = abs(hist['Close'] - hist['Open'])
        hist['Upper_Wick'] = hist['High'] - hist[['Close', 'Open']].max(axis=1)
        hist['Lower_Wick'] = hist[['Close', 'Open']].min(axis=1) - hist['Low']
        hist['Volume_MA'] = hist['Volume'].rolling(10).mean()
        hist['Volume_Ratio'] = hist['Volume'] / hist['Volume_MA']
        
        # Recent bars (last 10)
        recent = hist.tail(10)
        
        # Detect buying/selling pressure
        buying_bars = 0
        selling_bars = 0
        absorption_bars = 0
        
        for _, bar in recent.iterrows():
            price_change = ((bar['Close'] - bar['Open']) / bar['Open']) * 100
            
            if bar['Volume_Ratio'] > 1.2:  # High volume
                if price_change > 0.5:  # Price up
                    buying_bars += 1
                elif price_change < -0.5:  # Price down
                    selling_bars += 1
                elif abs(price_change) < 0.3:  # Price flat
                    absorption_bars += 1
        
        # Current market pressure
        if buying_bars > selling_bars * 1.5:
            pressure = "🟢 STRONG BUYING"
        elif buying_bars > selling_bars:
            pressure = "🟢 Buying"
        elif selling_bars > buying_bars * 1.5:
            pressure = "🔴 STRONG SELLING"
        elif selling_bars > buying_bars:
            pressure = "🔴 Selling"
        else:
            pressure = "⚪ Neutral"
        
        # Last bar analysis
        last_bar = recent.iloc[-1]
        last_price_change = ((last_bar['Close'] - last_bar['Open']) / last_bar['Open']) * 100
        
        # Order flow
        if last_bar['Volume_Ratio'] > 1.3 and last_price_change > 0:
            order_flow = "🔥 Aggressive Buying"
        elif last_bar['Volume_Ratio'] > 1.3 and last_price_change < 0:
            order_flow = "🔴 Aggressive Selling"
        elif absorption_bars >= 3:
            order_flow = "🟡 Absorption (Kuat Tahan)"
        else:
            order_flow = "⚪ Normal Flow"
        
        return {
            "ticker": ticker.replace('.JK', ''),
            "analysis_period": period,
            "current_pressure": {
                "pressure": pressure,
                "buying_bars": buying_bars,
                "selling_bars": selling_bars,
                "absorption_bars": absorption_bars
            },
            "order_flow": {
                "flow_type": order_flow,
                "last_bar_volume_ratio": round(last_bar['Volume_Ratio'], 2),
                "last_bar_change_pct": round(last_price_change, 2)
            },
            "last_bar_details": {
                "open": round(last_bar['Open'], 2),
                "high": round(last_bar['High'], 2),
                "low": round(last_bar['Low'], 2),
                "close": round(last_bar['Close'], 2),
                "volume": int(last_bar['Volume']),
                "spread_pct": round(last_bar['Spread'], 2),
                "body_size": round(last_bar['Body'], 2),
                "upper_wick": round(last_bar['Upper_Wick'], 2),
                "lower_wick": round(last_bar['Lower_Wick'], 2)
            },
            "interpretation": {
                "dominant_force": "BUYERS" if buying_bars > selling_bars else "SELLERS" if selling_bars > buying_bars else "BALANCED",
                "market_sentiment": "BULLISH" if buying_bars > selling_bars * 1.2 else "BEARISH" if selling_bars > buying_bars * 1.2 else "NEUTRAL",
                "immediate_action": "BUY" if pressure in ["🟢 STRONG BUYING", "🟢 Buying"] else "SELL" if "SELLING" in pressure else "WAIT"
            }
        }
        
    except Exception as e:
        return {"error": str(e)}



# ==================== MCP TOOL WRAPPERS ====================

def get_foreign_flow_tool() -> Tool:
    """Get tool definition for foreign flow analysis."""
    return Tool(
        name="get_foreign_flow",
        description="Analisis aliran dana asing (foreign flow) dan institusi. Mendeteksi akumulasi/distribusi dari smart money.",
        inputSchema={
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Ticker saham IDX (contoh: BBRI, BBCA, TLKM)"
                },
                "period": {
                    "type": "string",
                    "description": "Periode analisis (default: 1mo). Pilihan: 7d, 1mo, 3mo, 6mo",
                    "default": "1mo"
                }
            },
            "required": ["ticker"]
        }
    )


async def get_foreign_flow(arguments: dict) -> dict:
    """Handle foreign flow analysis request."""
    ticker = arguments.get("ticker")
    period = arguments.get("period", "1mo")
    
    result = analyze_foreign_flow(ticker, period)
    return result


def get_bandarmology_tool() -> Tool:
    """Get tool definition for bandarmology analysis."""
    return Tool(
        name="get_bandarmology",
        description="Analisis bandarmology - deteksi fase akumulasi/markup/distribusi/markdown berdasarkan price-volume action.",
        inputSchema={
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Ticker saham IDX (contoh: BBRI, BBCA, TLKM)"
                },
                "period": {
                    "type": "string",
                    "description": "Periode analisis (default: 3mo). Pilihan: 1mo, 3mo, 6mo, 1y",
                    "default": "3mo"
                }
            },
            "required": ["ticker"]
        }
    )


async def get_bandarmology(arguments: dict) -> dict:
    """Handle bandarmology analysis request."""
    ticker = arguments.get("ticker")
    period = arguments.get("period", "3mo")
    
    result = analyze_bandarmology(ticker, period)
    return result


def get_tape_reading_tool() -> Tool:
    """Get tool definition for tape reading analysis."""
    return Tool(
        name="get_tape_reading",
        description="Analisis tape reading - membaca order flow dan pressure dari price & volume action intraday.",
        inputSchema={
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Ticker saham IDX (contoh: BBRI, BBCA, TLKM)"
                },
                "period": {
                    "type": "string",
                    "description": "Periode analisis (default: 5d untuk intraday). Pilihan: 1d, 5d, 1mo",
                    "default": "5d"
                }
            },
            "required": ["ticker"]
        }
    )


async def get_tape_reading(arguments: dict) -> dict:
    """Handle tape reading analysis request."""
    ticker = arguments.get("ticker")
    period = arguments.get("period", "5d")
    
    result = analyze_tape_reading(ticker, period)
    return result

