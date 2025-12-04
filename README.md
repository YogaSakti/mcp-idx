# MCP Server: IDX Stock Data

MCP (Model Context Protocol) server untuk menghubungkan AI dengan data saham Indonesia (IDX) secara real-time. Server ini kompatibel dengan berbagai AI clients yang mendukung MCP seperti Claude Desktop, Cline, Continue, dan lainnya.

Server ini memungkinkan AI untuk mengakses data harga, historical chart, indikator teknikal, dan informasi fundamental saham melalui protokol MCP standar.

## 🚀 Quick Start (Lokal)

### 1. Install Dependencies

```bash
# Buat virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# atau: venv\Scripts\activate  # Windows

# Install packages
pip install -r requirements.txt
```

### 2. Test Server

```bash
python3 -m src.server
```

Tekan `Ctrl+C` untuk stop.

### 3. Setup AI Client

Server ini kompatibel dengan berbagai AI clients yang mendukung MCP. Pilih sesuai yang kamu pakai:

#### 🤖 Claude Desktop

Tambahkan ke `claude_desktop_config.json`:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`  
**Linux:** `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "idx-stocks": {
      "command": "python3",
      "args": ["-m", "src"],
      "cwd": "/path/to/mcp-idx",
      "env": {
        "CACHE_ENABLED": "true",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

#### 💻 Cline (VS Code Extension)

Tambahkan ke settings.json atau `.cline/mcp.json`:

```json
{
  "mcpServers": {
    "idx-stocks": {
      "command": "python3",
      "args": ["-m", "src"],
      "cwd": "/path/to/mcp-idx"
    }
  }
}
```

#### 🔄 Continue (VS Code Extension)

Tambahkan ke `.continue/config.json`:

```json
{
  "mcpServers": {
    "idx-stocks": {
      "command": "python3",
      "args": ["-m", "src"],
      "cwd": "/path/to/mcp-idx"
    }
  }
}
```

#### 🌐 Lainnya

Untuk AI clients lain yang support MCP, konfigurasinya umumnya sama:
- `command`: Path ke Python executable
- `args`: `["-m", "src"]`
- `cwd`: Path absolut ke folder project

**Penting:** Ganti `/path/to/mcp-idx` dengan path absolut ke folder project kamu.

Jika pakai venv, gunakan path ke Python di venv:
```json
{
  "mcpServers": {
    "idx-stocks": {
      "command": "/path/to/mcp-idx/venv/bin/python",
      "args": ["-m", "src"],
      "cwd": "/path/to/mcp-idx"
    }
  }
}
```

### 4. Restart AI Client

Restart aplikasi AI client kamu. Server akan start otomatis saat AI client terhubung.

📖 **Detail setup lengkap:** Lihat [LOCAL_SETUP.md](LOCAL_SETUP.md)

## ✨ Features

- 📊 **Real-time Stock Prices** - Harga saham terkini dengan perubahan harian
- 📈 **Historical Data** - Data OHLCV untuk charting dan analisis
- 🔍 **Technical Indicators** - RSI, MACD, SMA, EMA, Bollinger Bands, ADX, Ichimoku, dll
- 📐 **Fibonacci Levels** - Retracement & extension levels untuk support/resistance
- ⚡ **MA Crossovers** - Golden Cross, Death Cross, dan EMA crossover detection
- 🕯️ **Candlestick Patterns (NEW!)** - Doji, Hammer, Engulfing, Morning/Evening Star detection
- 💼 **Stock Information** - Informasi fundamental perusahaan
- 🔎 **Stock Search** - Cari saham berdasarkan nama atau ticker
- 📉 **Market Summary** - Ringkasan IHSG, top gainers/losers
- ⚖️ **Stock Comparison** - Bandingkan performa beberapa saham
- 📋 **Watchlist** - Ambil harga multiple tickers sekaligus

## 🤖 Compatible AI Clients

Server ini menggunakan **MCP (Model Context Protocol)** standar, sehingga kompatibel dengan berbagai AI clients:

- 🤖 **Claude Desktop** - Official Claude app dari Anthropic
- 💻 **Cline** - VS Code extension untuk AI coding assistant
- 🔄 **Continue** - VS Code extension dengan MCP support
- 🌐 **AI clients lain** yang implement MCP protocol

MCP adalah protokol open-source yang memungkinkan AI clients berkomunikasi dengan external tools dan data sources secara standar. Server ini mengikuti spesifikasi MCP, jadi bisa dipakai dengan AI client apapun yang support MCP!

## 🛠 Tech Stack

- Python 3.11+
- MCP SDK - Official Python SDK
- yfinance - Yahoo Finance API wrapper
- pandas-ta - Technical analysis library
- pydantic - Data validation
- cachetools - Caching layer

## 📚 Available Tools

**Total: 23 tools** (9 new: Foreign Flow, Bandarmology, Tape Reading, Financial Statements, Earnings Growth, Analyst Ratings, Dividend History, **Breakout Detection**, **Divergence Detection**)

> **ℹ️ Format Ticker:** Input ticker bisa dengan atau tanpa suffix `.JK` (sistem otomatis menambahkan suffix jika tidak ada)  
> Contoh: `BBCA`, `BBRI`, `TLKM` atau `BBCA.JK`, `BBRI.JK`, `TLKM.JK`

### 1. `get_stock_price`
Harga saham terkini beserta perubahan harian.
- `ticker` (required): Ticker IDX, contoh "BBCA" atau "BBCA.JK"

### 2. `get_historical_data`
Data OHLCV untuk charting.
- `ticker` (required): Ticker IDX
- `period` (optional): 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max
- `interval` (optional): 1d, 1wk, 1mo

### 3. `get_technical_indicators` **(UPDATED!)**
Indikator teknikal untuk analisis - **OPTIMIZED FOR IDX MARKET**.
- `ticker` (required): Ticker IDX
- `indicators` (optional): rsi, macd, sma_20, ema_50, bbands, stoch, atr, obv, vwap, **adx**, **ichimoku**
- `period` (optional): 1mo, 3mo, 6mo, 1y

**IDX-Specific Improvements:**
- RSI interpretation adjusted (RSI 70-80 di IDX masih bisa momentum)
- RSI >80 baru dianggap extreme overbought
- Dynamic MA alignment scoring (tidak hardcode 3 MA)
- NaN guards untuk data yang tidak lengkap
- Data sorting (ascending) untuk kalkulasi indikator yang akurat

**ADX (Average Directional Index)**
- Mengukur kekuatan trend (strong, developing, weak)
- Menentukan arah trend (bullish/bearish)
- +DI dan -DI untuk konfirmasi
- Interpretasi: ADX > 25 = strong trend, < 20 = weak/sideways

**Ichimoku Cloud**
- 5 komponen: Tenkan-sen, Kijun-sen, Senkou Span A/B, Chikou Span
- Cloud color (bullish/bearish)
- Price vs Cloud position (above/inside/below)
- TK Cross signal
- Overall trend signal (strong_bullish, bullish, neutral, bearish, strong_bearish)

**Bollinger Bands (UPDATED)**
- Added BB position % (0-100, posisi harga dalam band)
- Added BB width untuk volatility measurement

### 4. `get_fibonacci_levels` **(UPDATED!)**
Fibonacci retracement dan extension levels untuk support/resistance analysis.
- `ticker` (required): Ticker IDX
- `period` (optional): 1mo, 3mo, 6mo, 1y (default: 3mo)
- `trend` (optional): 'auto', 'uptrend', atau 'downtrend' (default: auto)

**Features:**
- Auto-detect swing high/low
- 7 Retracement levels (0%, 23.6%, 38.2%, 50%, 61.8%, 78.6%, 100%)
- **4 Extension levels (127.2%, 161.8%, 200%, 261.8%)** - Added 261.8% untuk IDX yang sering ARA beruntun
- Nearest support/resistance identification
- Risk/reward ratio calculation
- Trading insights & recommendations
- **Fixed:** Extension formula sekarang mathematically correct

### 5. `get_ma_crossovers` **(NEW!)**
Detect Moving Average crossovers untuk trading signals.
- `ticker` (required): Ticker IDX
- `period` (optional): 3mo, 6mo, 1y (default: 6mo)
- `lookback_days` (optional): Days to look back for crossovers (default: 30)

**Features:**
- Golden Cross / Death Cross detection (SMA 50 x SMA 200)
- EMA 12 x EMA 26 crossovers
- Current MA alignment (bullish/bearish)
- Recent crossover history dengan dates
- Trading insights & momentum analysis

### 6. `get_candlestick_patterns` **(NEW!)**
Detect candlestick patterns untuk reversal & continuation signals.
- `ticker` (required): Ticker IDX
- `period` (optional): 1mo, 3mo, 6mo (default: 1mo)
- `lookback_days` (optional): Days to look back for patterns (default: 10)

**Supported Patterns:**
- **Single Candle**: Doji, Hammer, Shooting Star
- **Two Candle**: Bullish/Bearish Engulfing
- **Three Candle**: Morning Star, Evening Star

**Features:**
- Pattern detection dengan strength rating (medium, strong, very_strong)
- Signal classification (bullish, bearish, neutral)
- Pattern summary (bullish/bearish/neutral counts)
- Trading insights & reversal signals

### 7. `get_stock_info`
Informasi fundamental perusahaan.
- `ticker` (required): Ticker IDX

### 8. `search_stocks`
Cari saham berdasarkan nama atau ticker.
- `query` (required): Kata kunci pencarian
- `limit` (optional): Max hasil (default: 10)
- `sector` (optional): Filter sektor

### 9. `get_market_summary`
Ringkasan pasar IHSG dan top movers.
- `include_movers` (optional): Include gainers/losers (default: true)
- `movers_limit` (optional): Jumlah movers (default: 5)

### 10. `compare_stocks`
Bandingkan performa beberapa saham.
- `tickers` (required): List ticker saham
- `period` (optional): 1mo, 3mo, 6mo, 1y
- `metrics` (optional): performance, valuation, dividend

### 11. `get_watchlist_prices`
Harga untuk multiple tickers sekaligus.
- `tickers` (required): List ticker saham

### 12. `get_financial_ratios`
Analisis rasio keuangan fundamental lengkap.
- `ticker` (required): Ticker saham IDX
- Menghitung: P/E, P/B, P/S, ROE, ROA, Debt-to-Equity, Current Ratio, Quick Ratio, Dividend Yield, Growth metrics, dll
- Termasuk interpretasi untuk setiap ratio dan financial score

### 13. `get_volume_analysis`
Analisis volume trading saham.
- `ticker` (required): Ticker saham IDX
- `period` (optional): Periode analisis (7d, 30d, 90d, 1mo, 3mo, 6mo, 1y) - default: 30d
- Menghitung: Average volume, volume spikes, volume trend, volume-price correlation, unusual volume detection

### 14. `get_volatility_analysis`
Analisis volatilitas saham.
- `ticker` (required): Ticker saham IDX
- `period` (optional): Periode analisis (30d, 90d, 1y, 2y) - default: 1y
- Menghitung: Historical volatility (30d, 90d, 1y), Beta vs IHSG, ATR-based volatility, Risk level assessment

### 15. `get_foreign_flow` **(UPDATED! 🔥)**
Analisis Smart Money Proxy berdasarkan volume-price action.

⚠️ **DISCLAIMER:** Ini BUKAN real foreign net buy/sell dari BEI. Data institutional dari yfinance sering kosong untuk saham IDX. Tool ini fokus ke volume-price pattern untuk deteksi akumulasi/distribusi.

- `ticker` (required): Ticker saham IDX
- `period` (optional): 7d, 1mo, 3mo, 6mo (default: 1mo)

**Features:**
- Institutional proxy data (dengan disclaimer)
- Accumulation/Distribution pattern detection
- Volume trend analysis
- Smart Money Proxy score (berdasarkan volume-price action)
- Division by zero guards untuk stability

### 16. `get_bandarmology` **(UPDATED! 🔥)**
Deteksi fase akumulasi/distribusi bandar - **OPTIMIZED FOR IDX MARKET**.
- `ticker` (required): Ticker saham IDX
- `period` (optional): 1mo, 3mo, 6mo, 1y (default: 3mo)

**Features:**
- 4 Phase detection: ACCUMULATION, MARKUP, DISTRIBUTION, MARKDOWN
- 3 Volume Regime: LOW (<0.8x), NEUTRAL (0.8-1.2x), HIGH (>1.2x)
- Phase strength & confidence rating
- Price-volume action analysis
- Bandar strength score
- **NEW: ARA/ARB Detection** (Auto Rejection Atas/Bawah)
  - Support tick size (fraksi harga IDX)
  - Support FCA board (Papan Pemantauan Khusus, ±10%)
  - Floor price handling (Rp50 regular, Rp1 PPK)
- Trading recommendation dengan risk level

### 17. `get_tape_reading` **(NEW! 🔥)**
Membaca order flow & pressure real-time.
- `ticker` (required): Ticker saham IDX
- `period` (optional): 1d, 5d, 1mo (default: 5d untuk intraday)

**Features:**
- Buying/Selling pressure detection
- Order flow analysis (aggressive buying/selling)
- Absorption detection (strong support/resistance)
- Last bar details (OHLC, volume, spread, wicks)
- Immediate action recommendation

### 18. `get_financial_statements` **(NEW! 💰)**
Analisis laporan keuangan lengkap.
- `ticker` (required): Ticker saham IDX
- `period_type` (optional): quarterly, annual (default: annual)

**Features:**
- Income Statement: Revenue, Gross/Operating/Net Income, Margins
- Balance Sheet: Assets, Liabilities, Equity, Liquidity Ratios
- Cash Flow: Operating/Investing/Financing, Free Cash Flow
- Financial Health Score (0-100) dengan rating
- Multi-period comparison (up to 5 periods)

### 19. `get_earnings_growth` **(NEW! 📈)**
Analisis pertumbuhan earnings historis.
- `ticker` (required): Ticker saham IDX

**Features:**
- Historical earnings (Revenue, Net Income, EBITDA)
- Year-over-Year growth rates
- CAGR (Compound Annual Growth Rate)
- Growth rating: Explosive/Strong/Moderate/Slow/Negative
- Multi-year trend analysis

### 20. `get_analyst_ratings` **(NEW! 👥)**
Konsensus analyst & earnings estimates.
- `ticker` (required): Ticker saham IDX

**Features:**
- Analyst recommendations: Strong Buy/Buy/Hold/Sell breakdown
- Consensus rating dengan interpretasi
- Earnings & Revenue estimates dengan YoY growth
- Target price range (Low/Avg/High)
- Earnings calendar: Next report date & estimates

### 21. `get_dividend_history` **(NEW! 💵)**
Analisis historis dividen & yield.
- `ticker` (required): Ticker saham IDX

**Features:**
- Dividend payment history (dates & amounts)
- Dividend yield calculation
- Annual dividend & YoY growth
- Consistency rating: High/Medium/Low
- Years of continuous payments
- Dividend rating: Excellent/Good/Fair/Poor/No Dividend

### 22. `get_breakout_detection` **(NEW! 🚀)**
Detect price breakout dari consolidation range.
- `ticker` (required): Ticker saham IDX
- `lookback` (optional): Periode lookback untuk consolidation range (default: 20)
- `period` (optional): Periode data (default: 3mo)
- `volume_threshold` (optional): Volume multiplier untuk konfirmasi (default: 1.5x)

**Features:**
- Consolidation range detection (support/resistance)
- Breakout type: resistance_breakout, support_breakdown, testing_resistance, testing_support, inside_range
- Breakout strength: strong, moderate, weak
- Volume confirmation (1.5x+ average volume)
- Target prices (61.8%, 100%, 161.8% range projection)
- Stop loss calculation
- Risk/Reward ratio
- False breakout warning detection (rejection, decreasing volume, long wicks)
- Trading signal dengan confidence level

**Use Case:** Entry signal untuk momentum trading, detect potential breakout sebelum terjadi.

### 23. `get_divergence_detection` **(NEW! 📉📈)**
Detect divergence antara harga dan indikator (RSI, MACD, OBV).
- `ticker` (required): Ticker saham IDX
- `indicators` (optional): Indikator untuk cek divergence - rsi, macd, obv (default: semua)
- `lookback` (optional): Periode lookback (default: 30)
- `period` (optional): Periode data (default: 3mo)

**Features:**
- **Regular Divergence** (Reversal signals):
  - Bullish: Price lower low + Indicator higher low → Potential UP reversal
  - Bearish: Price higher high + Indicator lower high → Potential DOWN reversal
- **Hidden Divergence** (Continuation signals):
  - Bullish Hidden: Price higher low + Indicator lower low → Uptrend continues
  - Bearish Hidden: Price lower high + Indicator higher high → Downtrend continues
- Multi-indicator analysis (RSI, MACD Histogram, OBV)
- Divergence strength rating (strong, moderate, weak)
- Active divergence detection (recent, still valid)
- Overall signal dengan confidence level
- Indicator agreement check

**Use Case:** Early warning signal untuk potential reversal SEBELUM terjadi. Combine dengan S/R dan volume untuk konfirmasi.

## 💬 Usage Examples

Setelah terhubung dengan AI client kamu, coba tanyakan:

1. "Berapa harga BBCA sekarang?"
2. "Tampilkan chart BBRI 3 bulan terakhir"
3. "Analisa teknikal TLKM dengan RSI dan MACD"
4. "Bandingkan performa BBCA vs BBRI vs BMRI dalam setahun"
5. "Cari saham sektor banking dengan market cap terbesar"
6. "Gimana kondisi IHSG hari ini?"
7. "Apa saja top gainers hari ini?"
8. "Analisa foreign flow BBRI, apa institusi lagi akumulasi?" **(NEW!)**
9. "Cek bandarmology TLKM, lagi fase apa sekarang?" **(NEW!)**
10. "Tape reading ASII, ada buying pressure gak?" **(NEW!)**
11. "Analisa laporan keuangan BBCA.JK, gimana kesehatan finansialnya?" **(NEW!)**
12. "Berapa CAGR earnings BBRI.JK dalam 3 tahun terakhir?" **(NEW!)**
13. "Apa konsensus analyst untuk TLKM.JK? Buy atau sell?" **(NEW!)**
14. "Berapa dividend yield BBCA.JK? Konsisten gak bayar dividennya?" **(NEW!)**

## ⚙️ Configuration (Optional)

Environment variables yang bisa di-set:

```env
YAHOO_TIMEOUT=30              # Timeout untuk Yahoo Finance API
CACHE_ENABLED=true            # Enable caching
CACHE_MAX_SIZE=1000           # Max cache entries
RATE_LIMIT_REQUESTS=100       # Max requests
RATE_LIMIT_PERIOD=60          # Per period (seconds)
LOG_LEVEL=INFO                # Logging level
LOG_FILE=idx-stock-mcp.log    # Log file path
```

## ⚠️ Error Handling

Error codes yang mungkin muncul:
- `INVALID_TICKER` - Ticker tidak ditemukan
- `MARKET_CLOSED` - Pasar tutup
- `RATE_LIMITED` - Terlalu banyak request
- `DATA_UNAVAILABLE` - Data tidak tersedia
- `NETWORK_ERROR` - Gagal koneksi
- `INVALID_PARAMETER` - Parameter tidak valid

## 💾 Caching

| Data Type | TTL | Alasan |
|-----------|-----|--------|
| Current Price | 1 menit | Real-time data |
| Historical (intraday) | 5 menit | Update sepanjang hari |
| Historical (daily+) | 1 jam | Update harian |
| Stock Info | 24 jam | Jarang berubah |
| Search Results | 6 jam | Jarang berubah |
| Market Summary | 1 menit | Real-time data |

## 🧪 Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/
ruff check src/
```

## 📁 Project Structure

```
mcp-idx/
├── src/
│   ├── server.py              # MCP server utama
│   ├── server_http.py         # HTTP server (optional)
│   ├── tools/                 # Tool implementations (21 tools)
│   │   ├── price.py           # Current price
│   │   ├── info.py            # Stock info
│   │   ├── historical.py      # OHLCV data
│   │   ├── indicators.py      # Technical indicators (RSI, MACD, ADX, Ichimoku, dll)
│   │   ├── fibonacci.py       # Fibonacci levels
│   │   ├── ma_crossover.py    # MA crossover detection
│   │   ├── candlestick.py     # Candlestick patterns
│   │   ├── financial_ratios.py # Fundamental ratios
│   │   ├── volume_analysis.py  # Volume analysis
│   │   ├── volatility_analysis.py # Volatility metrics
│   │   ├── search.py          # Stock search
│   │   ├── market.py          # Market summary
│   │   ├── compare.py         # Stock comparison
│   │   ├── watchlist.py       # Watchlist prices
│   │   ├── foreign_flow.py    # Smart money analysis (NEW!)
│   │   └── fundamental.py     # Financial statements, earnings, analyst, dividend (NEW!)
│   ├── utils/                 # Utilities
│   │   ├── yahoo.py           # Yahoo Finance wrapper
│   │   ├── helpers.py         # Helper functions
│   │   ├── cache.py           # Caching layer
│   │   ├── validators.py      # Input validation
│   │   └── exceptions.py      # Custom exceptions
│   └── config/                # Configuration
│       ├── settings.py        # Settings
│       └── tickers.json       # IDX tickers
├── tests/                     # Test suite (14 test files)
│   ├── test_price.py
│   ├── test_validators.py
│   ├── test_helpers.py
│   ├── test_adx.py
│   ├── test_fibonacci.py
│   ├── test_ichimoku.py
│   ├── test_ma_crossover.py
│   ├── test_candlestick.py
│   ├── test_financial_ratios.py
│   ├── test_volume_analysis.py
│   ├── test_volatility_analysis.py
│   ├── test_foreign_flow.py   # Smart money tests (NEW!)
│   ├── test_fundamental.py    # Fundamental analysis tests (NEW!)
│   ├── stock_screener.py      # Stock screener with 4 strategies
│   └── stock_signal_now.py    # Signal generator for all sectors
├── requirements.txt
├── pyproject.toml
├── README.md
└── LOCAL_SETUP.md            # Setup guide detail
```

## 🔧 Troubleshooting

**Server tidak start?**
- Pastikan Python 3.11+ terinstall
- Cek path di config AI client kamu sudah benar (gunakan absolute path)
- Test manual: `python3 -m src.server`

**AI client tidak detect server?**
- Pastikan format config sesuai dengan AI client yang kamu pakai
- Cek log AI client untuk error messages
- Pastikan `cwd` menggunakan absolute path, bukan relative

**Import errors?**
- Pastikan dependencies terinstall: `pip install -r requirements.txt`
- Aktifkan venv jika pakai virtual environment
- Test import: `python3 -c "from src.server import server; print('OK')"`

**Path issues?**
- Gunakan **absolute path** untuk `cwd`, bukan relative
- Windows: gunakan `C:\\path\\to\\project` atau `C:/path/to/project`
- macOS/Linux: gunakan `/full/path/to/project`

**Tools tidak muncul di AI client?**
- Restart AI client sepenuhnya (quit dan buka lagi)
- Cek apakah server start dengan benar (lihat logs)
- Pastikan MCP protocol didukung oleh AI client kamu

Lihat [LOCAL_SETUP.md](LOCAL_SETUP.md) untuk troubleshooting lengkap.

---

## 📅 Changelog

### v1.2.0 (2 Dec 2025) - IDX Market Optimization
**Major Updates:**
- 🇮🇩 **IDX Market Optimization** - All tools sekarang optimized untuk karakteristik pasar Indonesia
- 🔧 **Fixed:** Fibonacci extension formula yang sebelumnya salah
- 🔧 **Fixed:** RSI interpretation untuk IDX (RSI 70-80 masih bisa momentum)
- 🔧 **Fixed:** Division by zero guards di semua tools
- 🔧 **Fixed:** Data sorting untuk kalkulasi indikator yang akurat

**New Features:**
- ⚡ **ARA/ARB Detection** - Auto Rejection Atas/Bawah dengan:
  - Tick size (fraksi harga) yang benar per range harga
  - Support FCA board (Papan Pemantauan Khusus, ±10%)
  - Floor price handling (Rp50 regular, Rp1 PPK)
- 📊 **Dynamic MA Alignment** - Scoring berdasarkan MA yang tersedia
- 📈 **BB Position %** - Posisi harga dalam Bollinger Band (0-100%)
- 🎯 **Fibonacci 261.8%** - Extension level tambahan untuk saham ARA beruntun

**Label Changes:**
- `foreign_flow` → `smart_money_proxy` (lebih akurat karena bukan real BEI data)
- Added disclaimers untuk data yang sumbernya kurang reliable

---

## 📝 Disclaimer

Script ini dibuat dengan bantuan **Cursor** dan **Claude** (AI coding assistant). Jadi kalau ada bug, jangan salahin manusia doang ya! 😄

*Made with ❤️ (and a lot of AI assistance)*

