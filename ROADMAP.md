# Roadmap: IDX Stock MCP Server

Dokumen ini berisi rencana pengembangan tools analisis tambahan untuk IDX Stock MCP Server.

## 📊 Tools Analisis yang Sudah Tersedia

✅ **Current Price** - Harga real-time  
✅ **Historical Data** - Data OHLCV  
✅ **Technical Indicators** - RSI, MACD, SMA, EMA, Bollinger Bands, Stochastic, ATR, OBV, VWAP, ADX, Ichimoku Cloud  
✅ **Fibonacci Retracement** - Auto-calculate Fibonacci levels dengan swing detection  
✅ **Moving Average Crossovers** - Golden/Death Cross detection  
✅ **Candlestick Patterns** - Pattern recognition (Doji, Hammer, Engulfing, dll)  
✅ **Stock Info** - Informasi fundamental dasar  
✅ **Search** - Pencarian saham  
✅ **Market Summary** - Ringkasan IHSG dan top movers  
✅ **Compare Stocks** - Perbandingan performa  
✅ **Watchlist** - Multiple tickers sekaligus  
✅ **Financial Ratios** - Analisis rasio keuangan lengkap  
✅ **Volume Analysis** - Analisis volume trading  
✅ **Volatility Analysis** - Analisis volatilitas dan beta  

---

## 🎯 Rencana Pengembangan Tools Baru

### Tier 1: High Priority (High Value, Easy Implementation)

#### 1. 📈 Financial Ratios Analysis
**Status:** ✅ Completed  
**Priority:** High  
**Complexity:** Low-Medium

**Features:**
- P/E Ratio (Price-to-Earnings)
- P/B Ratio (Price-to-Book)
- ROE (Return on Equity)
- ROA (Return on Assets)
- Debt-to-Equity Ratio
- Current Ratio
- Dividend Yield
- Payout Ratio
- EPS Growth
- Revenue Growth

**Use Cases:**
- "Analisa fundamental BBCA dengan financial ratios"
- "Bandingkan P/E ratio BBCA vs BBRI"
- "Tampilkan semua financial ratios untuk TLKM"

**Implementation Notes:**
- Data tersedia dari Yahoo Finance
- Perlu parsing dari `info` data yang sudah ada
- Bisa extend dari `get_stock_info` atau buat tool baru

---

#### 2. 📊 Volume Analysis
**Status:** ✅ Completed  
**Priority:** High  
**Complexity:** Low

**Features:**
- Volume spike detection (vs average)
- Average volume (7d, 30d, 90d)
- Volume trend (increasing/decreasing)
- Volume-price correlation
- Volume ratio (current vs average)
- Unusual volume alerts

**Use Cases:**
- "Apakah volume trading BBRI hari ini abnormal?"
- "Tampilkan volume trend BBCA 30 hari terakhir"
- "Deteksi volume spike di TLKM"

**Implementation Notes:**
- Data sudah ada di historical data
- Perlu kalkulasi statistik sederhana
- Bisa jadi extension dari `get_historical_data`

---

#### 3. 📉 Volatility Analysis
**Status:** ✅ Completed  
**Priority:** High  
**Complexity:** Medium

**Features:**
- Historical volatility (30d, 90d, 1y)
- Beta (vs IHSG)
- ATR-based volatility
- Volatility ranking dalam sektor
- Volatility percentile
- Risk level indicator

**Use Cases:**
- "Seberapa volatil saham TLKM dibanding sektor?"
- "Hitung beta BBCA terhadap IHSG"
- "Ranking volatilitas saham banking"

**Implementation Notes:**
- Perlu data IHSG untuk beta calculation
- Historical volatility dari standard deviation returns
- Bisa extend dari `get_technical_indicators`

---

### Tier 2: Medium Priority (Useful, Medium Complexity)

#### 4. 🏢 Sector Analysis
**Status:** 🔜 Planned  
**Priority:** Medium  
**Complexity:** Medium

**Features:**
- Top performers per sektor
- Sector comparison (banking vs consumer)
- Sector rotation indicators
- Average sector metrics
- Sector performance ranking
- Sector correlation

**Use Cases:**
- "Bandingkan performa sektor banking vs consumer goods"
- "Top 5 saham di sektor technology"
- "Analisa rotasi sektor bulan ini"

**Implementation Notes:**
- Perlu mapping ticker ke sektor
- Perlu agregasi data multiple tickers
- Bisa extend dari `get_market_summary`

---

#### 5. 💰 Dividend Analysis
**Status:** 🔜 Planned  
**Priority:** Medium  
**Complexity:** Medium

**Features:**
- Dividend history (5 tahun)
- Dividend yield trend
- Ex-dividend dates
- Payout ratio analysis
- Dividend growth rate
- Dividend sustainability score

**Use Cases:**
- "History dividen dan yield BBCA 5 tahun terakhir"
- "Kapan ex-dividend date BBCA berikutnya?"
- "Analisa sustainability dividen BBRI"

**Implementation Notes:**
- Data tersedia dari Yahoo Finance
- Perlu parsing dividend history
- Bisa jadi tool baru atau extend `get_stock_info`

---

#### 6. 🔗 Correlation Analysis
**Status:** 🔜 Planned  
**Priority:** Medium  
**Complexity:** Medium-High

**Features:**
- Correlation matrix (multiple tickers)
- Correlation dengan IHSG
- Sector correlation
- Rolling correlation (30d, 90d)
- Correlation heatmap data

**Use Cases:**
- "Seberapa tinggi korelasi BBCA dengan BBRI?"
- "Bandingkan korelasi BBCA, BBRI, BMRI dengan IHSG"
- "Correlation matrix untuk portfolio saya"

**Implementation Notes:**
- Perlu kalkulasi correlation coefficient
- Perlu data historical untuk multiple tickers
- Bisa jadi tool baru atau extend `compare_stocks`

---

### Tier 3: Advanced Features (Complex but Powerful)

#### 7. 💼 Portfolio Analysis
**Status:** 🔜 Planned  
**Priority:** Low-Medium  
**Complexity:** High

**Features:**
- Portfolio P&L calculation
- Weighted average metrics
- Portfolio risk (volatility, beta)
- Allocation analysis
- Portfolio rebalancing suggestions
- Risk-adjusted returns (Sharpe ratio)

**Use Cases:**
- "Analisa portfolio saya: BBCA 40%, BBRI 30%, TLKM 30%"
- "Hitung total P&L portfolio saya"
- "Saran rebalancing portfolio"

**Implementation Notes:**
- Perlu input portfolio composition
- Perlu agregasi data multiple tickers
- Perlu kalkulasi weighted metrics
- Tool baru yang cukup kompleks

---

#### 8. ✨ Moving Average Crossovers
**Status:** ✅ Completed  
**Priority:** Low-Medium  
**Complexity:** Medium

**Features:**
- Golden Cross / Death Cross detection
- Multiple MA crossovers (SMA 50/200, EMA 12/26)
- Crossover signals dengan volume confirmation
- Crossover history
- Signal strength indicator

**Use Cases:**
- "Apakah BBCA menunjukkan golden cross?"
- "Deteksi semua crossover signals di BBRI"
- "Signal trading berdasarkan MA crossover"

**Implementation Notes:**
- Extend dari `get_technical_indicators`
- Perlu logic untuk detect crossovers
- Perlu historical data untuk backtesting

---

#### 9. 🎯 Price Targets & Levels
**Status:** 🔜 Planned  
**Priority:** Low  
**Complexity:** Medium-High

**Features:**
- Fibonacci retracement levels
- Pivot points (support/resistance)
- Price targets dari pattern
- Risk/reward ratio
- Multiple timeframe analysis

**Use Cases:**
- "Hitung price target dan support/resistance BBCA"
- "Fibonacci levels untuk BBRI"
- "Risk/reward ratio untuk entry di TLKM"

**Implementation Notes:**
- Perlu kalkulasi teknikal advanced
- Perlu pattern recognition
- Bisa extend dari support/resistance yang sudah ada

---

#### 10. 🕯️ Candlestick Patterns
**Status:** ✅ Completed
**Priority:** Low
**Complexity:** High

**Features:**
- Common patterns (Doji, Hammer, Engulfing, etc.)
- Pattern recognition dengan confidence
- Pattern success rate historis
- Multiple timeframe patterns
- Pattern alerts

**Use Cases:**
- "Deteksi candlestick patterns di BBRI minggu ini"
- "Apakah BBCA menunjukkan bullish engulfing?"
- "History success rate pattern hammer di TLKM"

**Implementation Notes:**
- Perlu pattern recognition algorithm
- Perlu historical pattern analysis
- Bisa pakai library seperti `ta-lib` atau custom logic
- Kompleksitas tinggi untuk accuracy

---

#### 11. 📊 ADX (Average Directional Index)
**Status:** ✅ Completed
**Priority:** Medium-High
**Complexity:** Medium

**Features:**
- ADX value untuk trend strength measurement
- +DI dan -DI indicators
- Trend strength classification (weak/strong/very strong)
- Multiple timeframe analysis
- Historical ADX trend

**Use Cases:**
- "Seberapa kuat trend BBCA saat ini?"
- "Apakah BBRI sedang trending atau sideways?"
- "Analisa trend strength untuk TLKM dengan ADX"

**Implementation Notes:**
- Extend dari `get_technical_indicators`
- Library pandas_ta sudah support ADX
- ADX > 25 = strong trend, < 20 = weak/no trend
- Bisa dikombinasi dengan MACD untuk konfirmasi trend

---

#### 12. ☁️ Ichimoku Cloud
**Status:** ✅ Completed
**Priority:** Medium
**Complexity:** Medium-High

**Features:**
- Tenkan-sen (Conversion Line)
- Kijun-sen (Base Line)
- Senkou Span A & B (Cloud)
- Chikou Span (Lagging Span)
- Cloud interpretation (bullish/bearish)
- Price position vs cloud

**Use Cases:**
- "Analisa Ichimoku untuk BBCA"
- "Apakah BBRI di atas atau di bawah cloud?"
- "Signal trading dari Ichimoku TLKM"

**Implementation Notes:**
- Popular di kalangan trader Indonesia
- Extend dari `get_technical_indicators`
- Bisa pakai pandas_ta atau custom calculation
- Kompleks karena multiple components

---

#### 13. 📐 Fibonacci Retracement
**Status:** ✅ Completed
**Priority:** High
**Complexity:** Medium

**Features:**
- Auto-calculate Fibonacci levels (23.6%, 38.2%, 50%, 61.8%, 78.6%)
- Based on recent swing high/low
- Support/resistance dari Fibo levels
- Multiple timeframe analysis
- Fibo extension levels

**Use Cases:**
- "Hitung Fibonacci retracement levels untuk BBCA"
- "Support resistance BBRI berdasarkan Fibonacci"
- "Price target TLKM dengan Fibonacci extension"

**Implementation Notes:**
- Tool baru: `get_fibonacci_levels`
- Auto-detect swing high/low dari historical data
- Bisa dikombinasi dengan support/resistance yang ada
- Sangat berguna untuk entry/exit points

---

#### 14. 📈 Chart Pattern Recognition
**Status:** 🔜 Planned
**Priority:** Medium
**Complexity:** High

**Features:**
- Head and Shoulders (regular & inverse)
- Double Top/Bottom
- Triangle patterns (ascending, descending, symmetrical)
- Flag and Pennant patterns
- Cup and Handle
- Wedge patterns
- Pattern confidence score

**Use Cases:**
- "Deteksi chart patterns di BBRI"
- "Apakah BBCA membentuk double top?"
- "Pattern apa yang terbentuk di TLKM saat ini?"

**Implementation Notes:**
- Tool baru: `detect_chart_patterns`
- Perlu advanced pattern matching algorithm
- Bisa combine dengan volume analysis untuk validation
- Kompleksitas sangat tinggi untuk accuracy
- Pertimbangkan pakai ML/AI untuk pattern recognition

---

### Tier 4: IDX-Specific Features (Khusus Market Indonesia)

#### 15. 🇮🇩 Foreign vs Domestic Flow
**Status:** ⚠️ Partially Implemented (Smart Money Proxy)
**Priority:** High
**Complexity:** High

**Current Implementation:**
- ✅ Smart Money Proxy berdasarkan volume-price action
- ✅ Accumulation/Distribution pattern detection
- ✅ Volume trend analysis
- ⚠️ **Note:** Bukan real foreign net buy/sell dari BEI

**Missing (Real Foreign Flow):**
- Daily foreign buy/sell value dari BEI
- Net foreign flow data
- Top foreign activity stocks
- Broker summary

**Use Cases:**
- "Berapa net foreign flow BBCA hari ini?" → ⚠️ Proxy only
- "Apakah asing sedang akumulasi atau distribusi di BBRI?" → ✅ Via volume pattern
- "Top 10 saham dengan foreign inflow terbesar" → ❌ Need BEI data

**Implementation Notes:**
- **Challenge:** Real data tidak tersedia di Yahoo Finance
- Current tool `get_foreign_flow` adalah PROXY, bukan real data
- Untuk real foreign flow, perlu:
  - Scraping dari IDX website atau RTI
  - Paid API (Bloomberg, Refinitiv, atau lokal seperti Pluang/Stockbit)

---

#### 16. 🏢 Broker Summary
**Status:** 🔜 Planned
**Priority:** Medium-High
**Complexity:** Very High

**Features:**
- Top buying brokers (by value)
- Top selling brokers (by value)
- Broker accumulation/distribution patterns
- Broker transaction history
- Net position per broker
- Smart money tracking

**Use Cases:**
- "Broker apa yang lagi beli BBCA hari ini?"
- "Tracking smart money di BBRI"
- "Analisa broker accumulation pattern TLKM"

**Implementation Notes:**
- **Challenge:** Data tidak tersedia di public API
- Perlu akses ke broker data feed atau paid services
- Mungkin perlu partnership dengan data provider
- Tool baru: `get_broker_summary`
- Sangat berguna tapi sulit implementasi (data availability)

---

#### 17. 📅 Corporate Actions
**Status:** 🔜 Planned
**Priority:** Medium
**Complexity:** Medium

**Features:**
- Stock split history dan schedule
- Dividend schedule (ex-date, payment date)
- Rights issue information
- Bonus shares announcements
- Warrant information
- Corporate action calendar

**Use Cases:**
- "Kapan jadwal dividen BBCA berikutnya?"
- "History stock split BBRI 5 tahun terakhir"
- "Corporate actions untuk TLKM bulan ini"

**Implementation Notes:**
- Partial data tersedia dari Yahoo Finance (dividend)
- Untuk data lengkap perlu scraping IDX announcements
- Tool baru: `get_corporate_actions`
- Extend dari dividend analysis yang sudah ada
- Bisa combine dengan existing `get_stock_info`

---

#### 18. 📊 Index Composition & Tracking
**Status:** 🔜 Planned
**Priority:** Medium
**Complexity:** Medium

**Features:**
- LQ45 members dan weights
- IDX30 members dan weights
- Sectoral indices composition
- Index rebalancing history
- Stock eligibility untuk index inclusion
- Index tracking error

**Use Cases:**
- "Apakah GOTO masuk LQ45?"
- "List semua saham di IDX30"
- "Kapan terakhir BBCA masuk/keluar dari index?"

**Implementation Notes:**
- Data bisa di-scrape dari IDX website
- Static data bisa hardcode, update quarterly
- Tool baru: `get_index_composition`
- Bisa dikombinasi dengan `search_stocks` dengan filter index

---

#### 19. 📡 Market Breadth Analysis
**Status:** 🔜 Planned
**Priority:** Medium
**Complexity:** Medium-High

**Features:**
- Advance/Decline ratio (jumlah saham naik vs turun)
- New 52-week highs/lows
- Volume leaders (most active by volume)
- Value leaders (most active by value)
- Market participation rate
- Breadth momentum indicators

**Use Cases:**
- "Berapa rasio advance/decline hari ini?"
- "Saham apa yang mencapai 52-week high?"
- "Most active stocks by volume hari ini"

**Implementation Notes:**
- Perlu data untuk semua saham IDX (700+ stocks)
- Bisa extend dari `get_market_summary`
- Tool baru: `get_market_breadth`
- Perlu efficient data fetching (batch processing)
- Cache heavily karena data market-wide

---

## 📅 Timeline Estimasi

### Phase 1: Foundation (Tier 1)
**Target:** 2-3 minggu
- ✅ Financial Ratios Analysis - **COMPLETED**
- ✅ Volume Analysis - **COMPLETED**
- ✅ Volatility Analysis - **COMPLETED**

**🎉 Phase 1 Complete!**

### Phase 2: Enhancement (Tier 2)
**Target:** 3-4 minggu
- ✅ Sector Analysis
- ✅ Dividend Analysis
- ✅ Correlation Analysis

### Phase 3: Advanced (Tier 3)
**Target:** 4-6 minggu
- 🔜 Portfolio Analysis
- 🔜 Moving Average Crossovers
- 🔜 Price Targets & Levels
- 🔜 Candlestick Patterns

### Phase 4: Technical Analysis Enhancement
**Target:** 3-4 minggu (Completed in 1 day!)
- ✅ ADX (Average Directional Index) - **COMPLETED**
- ✅ Fibonacci Retracement Levels - **COMPLETED**
- ✅ Ichimoku Cloud - **COMPLETED**
- ✅ Moving Average Crossovers - **COMPLETED**
- ✅ Candlestick Patterns - **COMPLETED**
- 🔜 Chart Pattern Recognition - **DEFERRED** (Optional)

**🎉 Phase 4 Complete!**

### Phase 5: IDX-Specific Features (Tier 4)
**Target:** 6-8 minggu (tergantung data availability)
- 🔜 Foreign vs Domestic Flow
- 🔜 Corporate Actions
- 🔜 Index Composition & Tracking
- 🔜 Market Breadth Analysis
- 🔜 Broker Summary (optional, perlu paid data)

---

## 🔧 Technical Considerations

### Dependencies yang Mungkin Diperlukan
- `scipy` - untuk statistical calculations (correlation, volatility)
- `numpy` - sudah ada, untuk advanced calculations
- `ta-lib` (optional) - untuk advanced technical analysis
- `scikit-learn` (optional) - untuk pattern recognition
- `beautifulsoup4` / `selenium` - untuk scraping IDX data (foreign flow, broker, corporate actions)

### Data Requirements
- Yahoo Finance API sudah cukup untuk sebagian besar tools
- Mungkin perlu data tambahan untuk:
  - Sector mapping (bisa hardcode atau dari Yahoo)
  - IHSG data untuk beta calculation
  - Dividend history (tersedia di Yahoo)
  - **IDX-specific data:**
    - Foreign flow: scraping dari IDX/RTI atau paid API
    - Broker summary: paid data feed (challenging)
    - Corporate actions: scraping IDX announcements
    - Index composition: scraping IDX atau hardcode quarterly update

### Performance Considerations
- Cache strategy untuk tools baru
- Batch processing untuk multiple tickers
- Async operations untuk correlation/portfolio analysis

---

## 📝 Notes

- Prioritas bisa berubah berdasarkan feedback user
- Beberapa tools bisa dikombinasikan (misalnya Financial Ratios + Dividend Analysis)
- Testing penting untuk tools yang kompleks (correlation, portfolio)
- Dokumentasi perlu diupdate setiap kali ada tool baru

---

## 🤝 Contributing

Ide tools baru atau improvement bisa ditambahkan di sini dengan format:
- **Tool Name**
- **Priority** (High/Medium/Low)
- **Complexity** (Low/Medium/High)
- **Use Cases**
- **Implementation Notes**

---

## 📊 Summary of New Additions for Indonesian Market

### ✅ Completed (Phase 4)
1. ✅ **ADX** - Trend strength indicator (pandas_ta support) - **COMPLETED**
2. ✅ **Fibonacci Retracement** - Price targets & entry/exit points - **COMPLETED**
3. ✅ **Ichimoku Cloud** - Popular di Indonesia - **COMPLETED**
4. ✅ **Moving Average Crossovers** - Golden/Death Cross detection - **COMPLETED**
5. ✅ **Candlestick Patterns** - Pattern recognition - **COMPLETED**

### 🔜 Planned (Easy + High Value)
6. **Corporate Actions** - Dividend schedule (partial dari Yahoo)

### Medium Implementation (Worth the Effort)
7. **Chart Patterns** - ML-based detection (deferred from Phase 4)
8. **Index Composition** - LQ45/IDX30 tracking

### Challenging (Data Availability Issues)
7. **Foreign Flow** - Perlu scraping atau paid API
8. **Broker Summary** - Perlu paid data feed
9. **Market Breadth** - Perlu data all IDX stocks

### Priority Recommendation

**✅ Phase 4 (Technical Enhancement) - COMPLETED!**
- Semua tools sudah diimplementasikan dan tested
- ADX, Fibonacci, Ichimoku, MA Crossovers, Candlestick Patterns sudah ready
- Chart Pattern Recognition di-defer (optional feature)

**Next: Phase 5 (IDX-Specific)** - Dikerjakan sambil riset data sources karena:
- Butuh data scraping atau paid API
- Implementation tergantung ketersediaan data
- Very valuable tapi more complex

---

---

## 🇮🇩 IDX Market Optimizations (2 Dec 2025)

### Completed Today:

#### Technical Indicators (`indicators.py`)
- ✅ RSI interpretation adjusted untuk IDX (RSI 70-80 masih momentum)
- ✅ Dynamic MA alignment scoring (tidak hardcode)
- ✅ NaN guards untuk semua indikator
- ✅ Data sorting fix (ascending untuk kalkulasi yang benar)
- ✅ Bollinger Bands position % dan width

#### Bandarmology (`foreign_flow.py`)
- ✅ 3 Volume Regime (LOW, NEUTRAL, HIGH)
- ✅ Improved MARKDOWN detection (multiple patterns)
- ✅ Division by zero guards
- ✅ **ARA/ARB Detection dengan:**
  - Tick size (fraksi harga) per range harga
  - FCA board support (Papan Pemantauan Khusus, ±10%)
  - Floor price (Rp50 regular, Rp1 PPK)
- ✅ Renamed labels ke "smart_money_proxy" (lebih akurat)

#### Fibonacci (`fibonacci.py`)
- ✅ Fixed extension formula (sebelumnya salah)
- ✅ Added 261.8% extension level untuk ARA beruntun

#### Volume Analysis (`volume_analysis.py`)
- ✅ Fixed division by zero handling

---

*Last Updated: 2025-12-02*

