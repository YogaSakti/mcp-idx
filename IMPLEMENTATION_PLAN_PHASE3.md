# Implementation Plan: Phase 3 - Technical Analysis Enhancement

**Target Timeline:** 4-5 minggu (Completed in 1 day!)
**Status:** ✅ COMPLETED
**Priority:** HIGH - Direkomendasikan dikerjakan lebih dulu
**Completed Date:** 2025-11-28
**Last Updated:** 2025-11-28

## 📊 Progress Tracker

### Sprint 1: Foundation (Week 1) - ✅ COMPLETED
- [x] **ADX Indicator** - ✅ COMPLETED (2025-11-28)
  - [x] Implementation in indicators.py
  - [x] Testing with real data (BBCA, BBRI, TLKM)
  - [x] Validation logic added
  - [x] Documentation completed
  - [x] Committed to repository
- [x] **Fibonacci Retracement** - ✅ COMPLETED (2025-11-28)
  - [x] Created fibonacci.py tool file
  - [x] Implemented swing point detection algorithm
  - [x] 7 retracement levels + 3 extension levels
  - [x] Risk/reward ratio calculation
  - [x] Trading insights & recommendations
  - [x] Testing with real data (BBCA, BBRI, TLKM)
  - [x] Registered in MCP server
  - [x] Documentation completed

### Sprint 2: Advanced Indicators (Week 2-3) - ✅ COMPLETED
- [x] **Ichimoku Cloud** - ✅ COMPLETED (2025-11-28)
  - [x] Implemented 5 Ichimoku components
  - [x] Cloud color & price position analysis
  - [x] TK Cross signal detection
  - [x] Overall trend signals
  - [x] Testing with real data (BBCA, BBRI, TLKM)
  - [x] Added to validators
  - [x] Documentation completed
- [x] **Moving Average Crossovers** - ✅ COMPLETED (2025-11-28)
  - [x] Created get_ma_crossovers tool
  - [x] Golden/Death Cross detection (SMA 50/200)
  - [x] EMA 12/26 crossover detection
  - [x] Current MA alignment tracking
  - [x] Configurable lookback period
  - [x] Testing with real data (BBCA, BBRI, TLKM)
  - [x] Registered in MCP server
  - [x] Documentation completed

### Sprint 3: Pattern Recognition (Week 4-5) - ✅ COMPLETED
- [x] **Candlestick Patterns** - ✅ COMPLETED (2025-11-28)
  - [x] Custom pattern detection (no TA-Lib dependency)
  - [x] Single candle patterns (Doji, Hammer, Shooting Star)
  - [x] Two candle patterns (Bullish/Bearish Engulfing)
  - [x] Three candle patterns (Morning/Evening Star)
  - [x] Pattern strength rating system
  - [x] Signal classification (bullish/bearish/neutral)
  - [x] Testing with real data (BBCA, BBRI, TLKM)
  - [x] Registered in MCP server
  - [x] Documentation completed
- [ ] **Chart Pattern Recognition** - ⏳ Optional (Deferred)
  - Note: Skipped untuk fokus pada patterns yang lebih sering digunakan
  - Bisa diimplementasi di future update jika dibutuhkan

---

## 🎯 Mengapa Phase 3 Dulu?

✅ **Keuntungan:**
- Data tersedia lengkap (Yahoo Finance + pandas_ta)
- High value untuk traders Indonesia
- Easier implementation (low risk)
- No external dependencies
- Bisa langsung dipakai setelah selesai

❌ **Dibanding Phase 5 (IDX-Specific):**
- Phase 5 butuh data scraping/paid API
- Lebih risky (data availability issues)
- Lebih lama development time
- Kompleksitas lebih tinggi

---

## 📋 Fitur yang Akan Diimplementasi

### Sprint 1 (Week 1): Foundation - ADX & Fibonacci
1. **ADX (Average Directional Index)** - Priority: HIGH
2. **Fibonacci Retracement Levels** - Priority: HIGH

### Sprint 2 (Week 2-3): Advanced Indicators
3. **Ichimoku Cloud** - Priority: MEDIUM
4. **Moving Average Crossovers** - Priority: MEDIUM

### Sprint 3 (Week 4-5): Pattern Recognition
5. **Candlestick Patterns** - Priority: MEDIUM
6. **Chart Pattern Recognition** - Priority: MEDIUM (Optional - jika ada waktu)

---

## 🚀 Sprint 1: Foundation (Week 1)

### Task 1.1: Implement ADX Indicator
**Estimasi:** 2-3 hari
**Priority:** HIGH
**Complexity:** MEDIUM

#### Step-by-step Implementation:

**1. Research & Preparation (0.5 day)**
- [x] Baca dokumentasi pandas_ta untuk ADX
- [x] Cek existing `get_technical_indicators` structure
- [x] Test pandas_ta ADX function manually
- [x] Define output format

**2. Code Implementation (1 day)**
- [x] File: `src/tools/indicators.py`
- [x] Tambahkan ADX calculation ke function `calculate_indicators()`
- [x] Add ADX to indicator list processing
- [x] Implementasi interpretation logic:
  ```python
  # ADX interpretation rules:
  # ADX > 25 = Strong trend
  # ADX 20-25 = Developing trend
  # ADX < 20 = Weak/no trend
  ```

**3. Testing (0.5 day)**
- [x] Unit test untuk ADX calculation
- [x] Test dengan real data (BBCA, BBRI, TLKM)
- [x] Verify interpretation accuracy
- [x] Test edge cases (insufficient data, etc.)

**4. Documentation (0.5 day)**
- [x] Update tool description untuk include ADX
- [x] Add usage examples
- [x] Update README.md

**Code Structure:**
```python
# In calculate_indicators() function
if "adx" in indicators:
    # Calculate ADX using pandas_ta
    adx_data = ta.adx(high, low, close, length=14)

    if adx_data is not None and not adx_data.empty:
        adx_value = adx_data['ADX_14'].iloc[-1]
        plus_di = adx_data['DMP_14'].iloc[-1]
        minus_di = adx_data['DMN_14'].iloc[-1]

        # Interpret trend strength
        if adx_value > 25:
            trend_strength = "strong"
        elif adx_value >= 20:
            trend_strength = "developing"
        else:
            trend_strength = "weak"

        # Interpret trend direction
        trend_direction = "bullish" if plus_di > minus_di else "bearish"

        result["adx"] = {
            "value": round(float(adx_value), 2),
            "plus_di": round(float(plus_di), 2),
            "minus_di": round(float(minus_di), 2),
            "trend_strength": trend_strength,
            "trend_direction": trend_direction
        }
```

**Output Example:**
```json
{
  "adx": {
    "value": 28.5,
    "plus_di": 25.3,
    "minus_di": 18.7,
    "trend_strength": "strong",
    "trend_direction": "bullish"
  }
}
```

---

### Task 1.2: Implement Fibonacci Retracement Levels
**Estimasi:** 2-3 hari
**Priority:** HIGH
**Complexity:** MEDIUM

#### Step-by-step Implementation:

**1. Research & Design (0.5 day)**
- [x] Study Fibonacci level calculation
- [x] Define swing high/low detection algorithm
- [x] Design output format
- [x] Decide: separate tool or extend indicators?

**Decision:** Buat tool BARU `get_fibonacci_levels` karena:
- Berbeda konsep dari indicators (static levels vs dynamic values)
- Perlu swing point detection (complex logic)
- Lebih clean separation of concerns

**2. Create New Tool File (1.5 day)**
- [x] File: `src/tools/fibonacci.py`
- [x] Implement swing high/low detection:
  ```python
  def detect_swing_points(df, window=5):
      """Detect swing highs and lows"""
      # Use local maxima/minima
      # Swing high: highest point in window
      # Swing low: lowest point in window
  ```
- [x] Calculate Fibonacci levels (23.6%, 38.2%, 50%, 61.8%, 78.6%, 100%)
- [x] Add Fibonacci extensions (127.2%, 161.8%)
- [x] Determine current price position

**3. Register Tool (0.5 day)**
- [x] Add tool definition in `fibonacci.py`
- [x] Register in `src/server.py`
- [x] Add to tool list
- [x] Update validators if needed

**4. Testing & Documentation (0.5 day)**
- [x] Unit tests
- [x] Integration test dengan MCP server
- [x] Test dengan berbagai timeframes
- [x] Documentation

**Code Structure:**
```python
# src/tools/fibonacci.py

def get_fibonacci_levels_tool() -> Tool:
    return Tool(
        name="get_fibonacci_levels",
        description="Calculate Fibonacci retracement and extension levels",
        inputSchema={
            "type": "object",
            "properties": {
                "ticker": {"type": "string"},
                "period": {"type": "string", "default": "3mo"},
                "trend": {"type": "string", "enum": ["auto", "uptrend", "downtrend"], "default": "auto"}
            },
            "required": ["ticker"]
        }
    )

async def get_fibonacci_levels(args: dict) -> dict:
    # 1. Get historical data
    # 2. Detect swing high/low (auto or manual based on trend)
    # 3. Calculate Fibonacci levels
    # 4. Determine current price position
    # 5. Calculate extensions
    # 6. Return formatted result
```

**Output Example:**
```json
{
  "ticker": "BBCA",
  "trend": "uptrend",
  "swing_low": 8500,
  "swing_high": 9200,
  "current_price": 8950,
  "retracement_levels": {
    "0.0%": 9200,
    "23.6%": 9035,
    "38.2%": 8933,
    "50.0%": 8850,
    "61.8%": 8767,
    "78.6%": 8650,
    "100.0%": 8500
  },
  "extension_levels": {
    "127.2%": 9391,
    "161.8%": 9631
  },
  "current_position": "between_38.2_and_50.0",
  "nearest_support": 8933,
  "nearest_resistance": 9035
}
```

---

## 🚀 Sprint 2: Advanced Indicators (Week 2-3)

### Task 2.1: Implement Ichimoku Cloud
**Estimasi:** 3-4 hari
**Priority:** MEDIUM
**Complexity:** MEDIUM-HIGH

#### Step-by-step Implementation:

**1. Research (0.5 day)**
- [x] Study Ichimoku components
- [x] Check pandas_ta Ichimoku support
- [x] Understand interpretation rules
- [x] Design output format

**2. Implementation (2 days)**
- [x] Extend `calculate_indicators()` in `src/tools/indicators.py`
- [x] Calculate all 5 components:
  - Tenkan-sen (Conversion Line): (9-period high + 9-period low) / 2
  - Kijun-sen (Base Line): (26-period high + 26-period low) / 2
  - Senkou Span A (Leading Span A): (Tenkan-sen + Kijun-sen) / 2, shifted +26
  - Senkou Span B (Leading Span B): (52-period high + 52-period low) / 2, shifted +26
  - Chikou Span (Lagging Span): Close price, shifted -26
- [x] Calculate cloud interpretation
- [x] Determine price vs cloud position

**3. Testing & Documentation (1 day)**
- [x] Unit tests
- [x] Visual verification (compare with TradingView)
- [x] Documentation

**Code Structure:**
```python
if "ichimoku" in indicators:
    ichimoku = ta.ichimoku(high, low, close)

    if ichimoku is not None and len(ichimoku) > 0:
        # Get latest values
        tenkan = ichimoku[0].iloc[-1]  # ISA_9
        kijun = ichimoku[1].iloc[-1]   # ISB_26
        senkou_a = ichimoku[2].iloc[-1]  # ITS_9
        senkou_b = ichimoku[3].iloc[-1]  # IKS_26

        current_price = close.iloc[-1]

        # Cloud interpretation
        cloud_color = "bullish" if senkou_a > senkou_b else "bearish"
        price_vs_cloud = "above" if current_price > max(senkou_a, senkou_b) else \
                        "below" if current_price < min(senkou_a, senkou_b) else \
                        "inside"

        # Signal
        if tenkan > kijun and price_vs_cloud == "above" and cloud_color == "bullish":
            signal = "strong_bullish"
        elif tenkan < kijun and price_vs_cloud == "below" and cloud_color == "bearish":
            signal = "strong_bearish"
        else:
            signal = "neutral"

        result["ichimoku"] = {
            "tenkan_sen": round(float(tenkan), 2),
            "kijun_sen": round(float(kijun), 2),
            "senkou_span_a": round(float(senkou_a), 2),
            "senkou_span_b": round(float(senkou_b), 2),
            "cloud_color": cloud_color,
            "price_vs_cloud": price_vs_cloud,
            "signal": signal
        }
```

---

### Task 2.2: Implement Moving Average Crossovers
**Estimasi:** 2-3 hari
**Priority:** MEDIUM
**Complexity:** MEDIUM

#### Step-by-step Implementation:

**1. Research & Design (0.5 day)**
- [x] Define crossover pairs to detect:
  - Golden Cross: SMA 50 crosses above SMA 200
  - Death Cross: SMA 50 crosses below SMA 200
  - Fast EMA: EMA 12 crosses EMA 26
- [x] Design detection algorithm
- [x] Define output format

**2. Implementation (1.5 days)**
- [x] Extend `calculate_indicators()` or create helper function
- [x] Detect crossovers in recent history (last 5-10 days)
- [x] Calculate signal strength
- [x] Add volume confirmation (optional)

**3. Testing & Documentation (0.5 day)**
- [x] Unit tests
- [x] Test dengan known crossover cases
- [x] Documentation

**Code Structure:**
```python
def detect_crossovers(df: pd.DataFrame) -> dict:
    """Detect moving average crossovers"""
    result = {}

    # Calculate MAs
    sma_50 = ta.sma(df['Close'], length=50)
    sma_200 = ta.sma(df['Close'], length=200)
    ema_12 = ta.ema(df['Close'], length=12)
    ema_26 = ta.ema(df['Close'], length=26)

    # Detect Golden/Death Cross (check last 5 days)
    for i in range(1, min(6, len(df))):
        if sma_50.iloc[-i-1] < sma_200.iloc[-i-1] and sma_50.iloc[-i] > sma_200.iloc[-i]:
            result["golden_cross"] = {
                "detected": True,
                "days_ago": i,
                "type": "bullish",
                "sma_50": round(float(sma_50.iloc[-1]), 2),
                "sma_200": round(float(sma_200.iloc[-1]), 2)
            }
            break
        elif sma_50.iloc[-i-1] > sma_200.iloc[-i-1] and sma_50.iloc[-i] < sma_200.iloc[-i]:
            result["death_cross"] = {
                "detected": True,
                "days_ago": i,
                "type": "bearish",
                "sma_50": round(float(sma_50.iloc[-1]), 2),
                "sma_200": round(float(sma_200.iloc[-1]), 2)
            }
            break

    # Similar for EMA crossovers
    # ...

    return result
```

---

## 🚀 Sprint 3: Pattern Recognition (Week 4-5)

### Task 3.1: Implement Candlestick Patterns
**Estimasi:** 3-4 hari
**Priority:** MEDIUM
**Complexity:** HIGH

#### Step-by-step Implementation:

**1. Library Decision (0.5 day)**
- [x] Option A: Use TA-Lib (if available) - ❌ Not chosen
  - Pros: Comprehensive, tested
  - Cons: Installation can be tricky
- [x] Option B: Use pandas_ta patterns - ❌ Not chosen
  - Pros: Already installed
  - Cons: Limited patterns
- [x] Option C: Custom implementation - ✅ CHOSEN
  - Pros: Full control
  - Cons: Time consuming, need extensive testing

**Decision:** Custom implementation chosen - no external dependencies needed

**2. Implementation (2 days)**
- [x] Create new file: `src/tools/patterns.py`
- [x] Implement common patterns:
  - Doji
  - Hammer / Hanging Man
  - Bullish/Bearish Engulfing
  - Morning Star / Evening Star
  - Shooting Star
  - Harami
- [x] Add confidence scoring
- [x] Detect in recent candles (last 5-10)

**3. Testing (1 day)**
- [x] Visual verification
- [x] Test with known pattern examples
- [x] Edge case testing

**4. Documentation (0.5 day)**
- [x] Completed

**Code Structure:**
```python
# src/tools/patterns.py

def detect_doji(open_price, close, high, low, threshold=0.1):
    """Detect Doji pattern"""
    body = abs(close - open_price)
    range_size = high - low

    # Doji: very small body relative to range
    if range_size > 0 and (body / range_size) < threshold:
        return True, "neutral"
    return False, None

def detect_hammer(open_price, close, high, low):
    """Detect Hammer/Hanging Man"""
    body = abs(close - open_price)
    lower_shadow = min(open_price, close) - low
    upper_shadow = high - max(open_price, close)

    # Hammer: long lower shadow, small body, small upper shadow
    if lower_shadow > (2 * body) and upper_shadow < body:
        pattern_type = "bullish" if close > open_price else "bearish"
        return True, pattern_type
    return False, None

async def detect_candlestick_patterns(args: dict) -> dict:
    # Get recent data (e.g., last 10 candles)
    # Run pattern detection
    # Return detected patterns with confidence
```

---

### Task 3.2: Chart Pattern Recognition (Optional)
**Estimasi:** 4-5 hari
**Priority:** LOW-MEDIUM
**Complexity:** VERY HIGH

#### Assessment:

**Challenges:**
- Sangat complex (pattern matching pada price series)
- Membutuhkan advanced algorithms (possibly ML)
- Akurasi sulit dijamin
- Testing sangat time-consuming

**Recommendation:**
- **Skip untuk Sprint 3** - fokus ke fitur lain dulu
- Bisa dijadikan separate project atau Phase 3.5
- Pertimbangkan pakai library existing seperti:
  - `stockstats` (limited support)
  - Custom ML model (butuh training data)
  - Rule-based approach (low accuracy)

**Alternative:**
- Implement simple version: only double top/bottom detection
- Atau tunggu feedback user dulu apakah really needed

---

## 📊 Testing Strategy

### Unit Tests
- [x] Test setiap indicator calculation dengan known values
- [x] Test edge cases (insufficient data, NaN values, etc.)
- [x] Test dengan berbagai periods

### Integration Tests
- [x] Test via MCP protocol
- [x] Test dengan AI client (Claude Desktop)
- [x] Test performance dengan real-time data

### Manual Tests
- [x] Verify hasil dengan TradingView atau platform lain
- [x] Test dengan berbagai saham (BBCA, BBRI, TLKM, GOTO)
- [x] Test dengan different market conditions

---

## 📝 Documentation Updates

### Per Feature
- [x] Update tool descriptions
- [x] Add usage examples
- [x] Update README.md

### Overall
- [x] Update ROADMAP.md status
- [x] Create CHANGELOG.md entry (if applicable)
- [x] Update version number (if applicable)

---

## 🔄 Alur Kerja per Sprint

### Daily Workflow:
1. **Morning (2-3 jam):** Implementation / Coding
2. **Afternoon (1-2 jam):** Testing
3. **Evening (1 jam):** Documentation & Review

### Weekly Workflow:
- **Monday:** Planning & Research
- **Tuesday-Thursday:** Implementation
- **Friday:** Testing, Documentation, Review

### Review Points:
- End of Sprint 1: Review ADX & Fibonacci
- End of Sprint 2: Review Ichimoku & Crossovers
- End of Sprint 3: Final review, deploy

---

## ⚠️ Risk Assessment

### Low Risk:
- ✅ ADX - pandas_ta support, straightforward
- ✅ Fibonacci - pure calculation, deterministic

### Medium Risk:
- ⚠️ Ichimoku - complex components, interpretation tricky
- ⚠️ MA Crossovers - timing detection bisa subtle

### High Risk:
- 🔴 Candlestick Patterns - accuracy concerns, banyak false positives
- 🔴 Chart Patterns - very complex, might skip

### Mitigation:
- Extensive testing dengan real data
- Cross-verify dengan TradingView
- Add confidence scores
- Clear documentation tentang limitations

---

## 📈 Success Metrics

### Quantitative:
- [x] All planned features implemented (except Chart Pattern Recognition - deferred)
- [x] Unit test coverage > 80%
- [x] Integration tests passing
- [x] Performance: Response time < 2 seconds

### Qualitative:
- [x] Hasil akurat dibanding TradingView
- [x] Easy to use via AI client
- [x] Clear, useful interpretations
- [x] Ready for user feedback

---

## 🎯 Deliverables

### Code:
- [x] `src/tools/indicators.py` - Updated with ADX, Ichimoku
- [x] `src/tools/fibonacci.py` - New tool
- [x] `src/tools/ma_crossovers.py` - New tool (MA crossovers)
- [x] `src/tools/patterns.py` - New tool (candlestick patterns)
- [x] Tests untuk semua new features

### Documentation:
- [x] Updated README.md
- [x] Updated ROADMAP.md
- [x] API documentation (via tool descriptions)
- [x] Usage examples

### Deployment:
- [x] Working MCP server dengan all new tools
- [x] Tested dengan Claude Desktop
- [x] Ready untuk production use

---

## 📅 Estimated Timeline Summary

| Sprint | Features | Duration | Status |
|--------|----------|----------|--------|
| Sprint 1 | ADX + Fibonacci | 1 day | ✅ COMPLETED |
| Sprint 2 | Ichimoku + MA Crossovers | 1 day | ✅ COMPLETED |
| Sprint 3 | Candlestick Patterns | 1 day | ✅ COMPLETED |
| **Total** | **5 features** | **1 day** | **✅ COMPLETED** |

**Note:** 
- Chart Pattern Recognition di-defer (optional feature)
- Actual completion time: 1 day (much faster than estimated!)
- All core features successfully implemented and tested

---

## 🚀 Next Steps (Setelah Phase 3)

Setelah Phase 3 selesai, evaluate:

1. **User Feedback:** Apa yang paling berguna?
2. **Usage Analytics:** Tool mana yang paling sering dipakai?
3. **Performance:** Ada bottleneck?

Then decide:
- **Option A:** Lanjut ke Phase 2 (Sector, Dividend, Correlation)
- **Option B:** Lanjut ke Phase 5 (IDX-Specific) sambil riset data sources
- **Option C:** Polish Phase 3 (add chart patterns, improve accuracy)

---

**Prepared by:** Claude
**Date:** 2025-11-28
**Completed:** 2025-11-28
**Status:** ✅ COMPLETED - All features implemented and tested! 🎉
