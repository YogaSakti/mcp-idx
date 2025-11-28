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
- 🔍 **Technical Indicators** - RSI, MACD, SMA, EMA, Bollinger Bands, dll
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

**Total: 11 tools**

### 1. `get_stock_price`
Harga saham terkini beserta perubahan harian.
- `ticker` (required): Ticker IDX, contoh "BBCA"

### 2. `get_historical_data`
Data OHLCV untuk charting.
- `ticker` (required): Ticker IDX
- `period` (optional): 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max
- `interval` (optional): 1d, 1wk, 1mo

### 3. `get_technical_indicators`
Indikator teknikal untuk analisis.
- `ticker` (required): Ticker IDX
- `indicators` (optional): rsi, macd, sma_20, ema_50, bbands, stoch, atr, obv, vwap
- `period` (optional): 1mo, 3mo, 6mo, 1y

### 4. `get_stock_info`
Informasi fundamental perusahaan.
- `ticker` (required): Ticker IDX

### 5. `search_stocks`
Cari saham berdasarkan nama atau ticker.
- `query` (required): Kata kunci pencarian
- `limit` (optional): Max hasil (default: 10)
- `sector` (optional): Filter sektor

### 6. `get_market_summary`
Ringkasan pasar IHSG dan top movers.
- `include_movers` (optional): Include gainers/losers (default: true)
- `movers_limit` (optional): Jumlah movers (default: 5)

### 7. `compare_stocks`
Bandingkan performa beberapa saham.
- `tickers` (required): List ticker saham
- `period` (optional): 1mo, 3mo, 6mo, 1y
- `metrics` (optional): performance, valuation, dividend

### 8. `get_watchlist_prices`
Harga untuk multiple tickers sekaligus.
- `tickers` (required): List ticker saham

### 9. `get_financial_ratios`
Analisis rasio keuangan fundamental lengkap.
- `ticker` (required): Ticker saham IDX
- Menghitung: P/E, P/B, P/S, ROE, ROA, Debt-to-Equity, Current Ratio, Quick Ratio, Dividend Yield, Growth metrics, dll
- Termasuk interpretasi untuk setiap ratio dan financial score

### 10. `get_volume_analysis`
Analisis volume trading saham.
- `ticker` (required): Ticker saham IDX
- `period` (optional): Periode analisis (7d, 30d, 90d, 1mo, 3mo, 6mo, 1y) - default: 30d
- Menghitung: Average volume, volume spikes, volume trend, volume-price correlation, unusual volume detection

### 11. `get_volatility_analysis`
Analisis volatilitas saham.
- `ticker` (required): Ticker saham IDX
- `period` (optional): Periode analisis (30d, 90d, 1y, 2y) - default: 1y
- Menghitung: Historical volatility (30d, 90d, 1y), Beta vs IHSG, ATR-based volatility, Risk level assessment

## 💬 Usage Examples

Setelah terhubung dengan AI client kamu, coba tanyakan:

1. "Berapa harga BBCA sekarang?"
2. "Tampilkan chart BBRI 3 bulan terakhir"
3. "Analisa teknikal TLKM dengan RSI dan MACD"
4. "Bandingkan performa BBCA vs BBRI vs BMRI dalam setahun"
5. "Cari saham sektor banking dengan market cap terbesar"
6. "Gimana kondisi IHSG hari ini?"
7. "Apa saja top gainers hari ini?"

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
│   ├── tools/                 # Tool implementations
│   │   ├── price.py
│   │   ├── historical.py
│   │   ├── indicators.py
│   │   ├── info.py
│   │   ├── search.py
│   │   ├── market.py
│   │   ├── compare.py
│   │   └── watchlist.py
│   ├── utils/                 # Utilities
│   │   ├── yahoo.py
│   │   ├── helpers.py
│   │   ├── cache.py
│   │   └── validators.py
│   └── config/                # Configuration
│       ├── settings.py
│       └── tickers.json
├── tests/                     # Test suite
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

## 📝 Disclaimer

Script ini dibuat dengan bantuan **Cursor** dan **Claude** (AI coding assistant). Jadi kalau ada bug, jangan salahin manusia doang ya! 😄

*Made with ❤️ (and a lot of AI assistance)*

