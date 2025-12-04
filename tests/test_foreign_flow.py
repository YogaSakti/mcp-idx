#!/usr/bin/env python3
"""
Test Foreign Flow, Bandarmology & Tape Reading Analysis
UPDATED: Matches new IDX-optimized output format with renamed fields.
"""

import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.foreign_flow import analyze_foreign_flow, analyze_bandarmology, analyze_tape_reading


def print_foreign_flow(ticker: str):
    """Test foreign flow (smart money proxy) analysis"""
    print("=" * 60)
    print(f"SMART MONEY PROXY ANALYSIS: {ticker}")
    print("=" * 60)
    
    result = analyze_foreign_flow(ticker, period="1mo")
    
    # Test JSON serialization
    try:
        json.dumps(result)
        print("✅ JSON serialization: OK")
    except Exception as e:
        print(f"❌ JSON serialization FAILED: {e}")
        return
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return
    
    print(f"\n📊 Ticker: {result['ticker']}")
    print(f"📅 Period: {result['analysis_period']}")
    print(f"📡 Data Source: {result.get('data_source', 'N/A')}")
    
    # NEW: institutional_proxy (renamed from foreign_ownership)
    print(f"\n💼 INSTITUTIONAL PROXY:")
    own = result.get('institutional_proxy', {})
    print(f"   ⚠️ Note: {own.get('note', 'N/A')}")
    print(f"   Insiders: {own.get('insiders_percent', 0):.2f}%")
    print(f"   Institutions: {own.get('institutions_percent', 0):.2f}%")
    print(f"   Float Institutions: {own.get('float_institutions_percent', 0):.2f}%")
    print(f"   Number of Institutions: {own.get('institutions_count', 0)}")
    
    # NEW: volume_flow_analysis (renamed from flow_analysis)
    print(f"\n📈 VOLUME FLOW ANALYSIS:")
    flow = result.get('volume_flow_analysis', {})
    print(f"   Trend: {flow.get('trend', 'N/A')}")
    print(f"   Accumulation Days: {flow.get('accumulation_days', 0)}")
    print(f"   Distribution Days: {flow.get('distribution_days', 0)}")
    print(f"   Net Pattern: {flow.get('net_pattern', 'N/A')}")
    
    print(f"\n📊 VOLUME METRICS:")
    vol = result.get('volume_metrics', {})
    print(f"   Average Volume: {vol.get('average_volume', 0):,}")
    print(f"   Recent Volume: {vol.get('recent_volume', 0):,}")
    print(f"   Trend: {vol.get('volume_trend_pct', 0):+.2f}% ({vol.get('volume_status', 'N/A')})")
    
    # NEW: smart_money_proxy (renamed from smart_money)
    print(f"\n💰 SMART MONEY PROXY:")
    sm = result.get('smart_money_proxy', {})
    print(f"   ⚠️ Note: {sm.get('note', 'N/A')}")
    print(f"   Score: {sm.get('score', 0)}/100")
    print(f"   Rating: {sm.get('rating', 'N/A')}")
    print(f"   Confidence: {sm.get('confidence', 'N/A')}")
    
    print(f"\n💡 INTERPRETATION:")
    interp = result.get('interpretation', {})
    print(f"   Ownership Level: {interp.get('ownership_level', 'N/A')}")
    print(f"   Institutional Interest: {interp.get('institutional_interest', 'N/A')}")
    print(f"   Pattern: {interp.get('pattern', 'N/A')}")
    
    print()


def print_bandarmology(ticker: str):
    """Test bandarmology analysis"""
    print("=" * 60)
    print(f"BANDARMOLOGY ANALYSIS: {ticker}")
    print("=" * 60)
    
    result = analyze_bandarmology(ticker, period="3mo")
    
    # Test JSON serialization
    try:
        json.dumps(result)
        print("✅ JSON serialization: OK")
    except Exception as e:
        print(f"❌ JSON serialization FAILED: {e}")
        return
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return
    
    print(f"\n📊 Ticker: {result['ticker']}")
    print(f"📅 Period: {result['analysis_period']}")
    
    print(f"\n🎯 CURRENT PHASE:")
    phase = result.get('current_phase', {})
    print(f"   Phase: {phase.get('phase', 'N/A')}")
    print(f"   Signal: {phase.get('signal', 'N/A')}")
    print(f"   Strength: {phase.get('strength', 0)}")
    print(f"   Confidence: {phase.get('confidence', 'N/A')}")
    print(f"   Margin vs 2nd: {phase.get('margin_vs_second', 0)}")
    
    print(f"\n📊 PHASE SCORES:")
    scores = result.get('phase_scores', {})
    print(f"   Accumulation: {scores.get('accumulation', 0)}")
    print(f"   Markup: {scores.get('markup', 0)}")
    print(f"   Distribution: {scores.get('distribution', 0)}")
    print(f"   Markdown: {scores.get('markdown', 0)}")
    
    print(f"\n💹 PRICE ACTION:")
    price = result.get('price_action', {})
    print(f"   Trend: {price.get('trend_pct', 0):+.2f}% ({price.get('trend_direction', 'N/A')})")
    print(f"   Current: {price.get('current_price', 0):,.0f}")
    print(f"   MA: {price.get('ma', 0):,.0f} (window: {price.get('ma_window', 'N/A')})")
    print(f"   MA Slope: {price.get('ma_slope', 0):+.2f}%")
    print(f"   Position: {price.get('position_vs_ma', 'N/A')}")
    
    print(f"\n📊 VOLUME ACTION:")
    vol = result.get('volume_action', {})
    print(f"   High Volume Days: {vol.get('high_volume_days', 0)}")
    print(f"   Neutral Volume Days: {vol.get('neutral_volume_days', 0)}")
    print(f"   Low Volume Days: {vol.get('low_volume_days', 0)}")
    print(f"   Volume Trend: {vol.get('volume_trend_pct', 0):+.2f}% ({vol.get('volume_status', 'N/A')})")
    
    print(f"\n🎲 BANDAR STRENGTH:")
    bandar = result.get('bandar_strength', {})
    print(f"   Score: {bandar.get('score', 0):.2f}")
    print(f"   Rating: {bandar.get('rating', 'N/A')}")
    print(f"   Active: {'YES' if bandar.get('active', False) else 'NO'}")
    
    # NEW: ARA/ARB Analysis
    print(f"\n🚀 ARA/ARB ANALYSIS:")
    ara = result.get('ara_arb_analysis', {})
    print(f"   Board Type: {ara.get('board_type', 'N/A')}")
    print(f"   ARA Hits: {ara.get('ara_hits', 0)}")
    print(f"   ARB Hits: {ara.get('arb_hits', 0)}")
    print(f"   Near ARA: {ara.get('near_ara', 0)}")
    print(f"   Near ARB: {ara.get('near_arb', 0)}")
    print(f"   Pattern: {ara.get('pattern', 'N/A')}")
    print(f"   Is Volatile: {ara.get('is_volatile', False)}")
    print(f"   Current ARA Limit: {ara.get('current_ara_limit', 0):,.0f}")
    print(f"   Current ARB Limit: {ara.get('current_arb_limit', 0):,.0f}")
    print(f"   Tick Size: {ara.get('tick_size', 'N/A')}")
    print(f"   Floor Price: {ara.get('floor_price', 'N/A')}")
    
    print(f"\n💡 RECOMMENDATION:")
    rec = result.get('recommendation', {})
    print(f"   Action: {rec.get('action', 'N/A')}")
    print(f"   Reason: {rec.get('reason', 'N/A')}")
    print(f"   Risk Level: {rec.get('risk_level', 'N/A')}")
    
    print()


def print_tape_reading(ticker: str):
    """Test tape reading analysis"""
    print("=" * 60)
    print(f"TAPE READING ANALYSIS: {ticker}")
    print("=" * 60)
    
    result = analyze_tape_reading(ticker, period="5d")
    
    # Test JSON serialization
    try:
        json.dumps(result)
        print("✅ JSON serialization: OK")
    except Exception as e:
        print(f"❌ JSON serialization FAILED: {e}")
        return
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return
    
    print(f"\n📊 Ticker: {result['ticker']}")
    print(f"📅 Period: {result['analysis_period']}")
    
    print(f"\n💪 CURRENT PRESSURE:")
    press = result.get('current_pressure', {})
    print(f"   Pressure: {press.get('pressure', 'N/A')}")
    print(f"   Buying Bars: {press.get('buying_bars', 0)}")
    print(f"   Selling Bars: {press.get('selling_bars', 0)}")
    print(f"   Absorption Bars: {press.get('absorption_bars', 0)}")
    
    print(f"\n🌊 ORDER FLOW:")
    flow = result.get('order_flow', {})
    print(f"   Flow Type: {flow.get('flow_type', 'N/A')}")
    print(f"   Last Bar Volume Ratio: {flow.get('last_bar_volume_ratio', 0):.2f}x")
    print(f"   Last Bar Change: {flow.get('last_bar_change_pct', 0):+.2f}%")
    
    print(f"\n📊 LAST BAR DETAILS:")
    bar = result.get('last_bar_details', {})
    print(f"   Open: {bar.get('open', 0):,.0f}")
    print(f"   High: {bar.get('high', 0):,.0f}")
    print(f"   Low: {bar.get('low', 0):,.0f}")
    print(f"   Close: {bar.get('close', 0):,.0f}")
    print(f"   Volume: {bar.get('volume', 0):,}")
    print(f"   Spread: {bar.get('spread_pct', 0):.2f}%")
    print(f"   Body: {bar.get('body_size', 0):.2f}")
    print(f"   Upper Wick: {bar.get('upper_wick', 0):.2f}")
    print(f"   Lower Wick: {bar.get('lower_wick', 0):.2f}")
    
    print(f"\n💡 INTERPRETATION:")
    interp = result.get('interpretation', {})
    print(f"   Dominant Force: {interp.get('dominant_force', 'N/A')}")
    print(f"   Market Sentiment: {interp.get('market_sentiment', 'N/A')}")
    print(f"   Immediate Action: {interp.get('immediate_action', 'N/A')}")
    
    print()


def test_json_serialization():
    """Test that all outputs can be JSON serialized."""
    print("\n" + "=" * 60)
    print("Testing JSON Serialization")
    print("=" * 60)
    
    ticker = "BBRI"
    all_ok = True
    
    # Test foreign flow
    result = analyze_foreign_flow(ticker)
    try:
        json.dumps(result)
        print("✅ analyze_foreign_flow: OK")
    except Exception as e:
        print(f"❌ analyze_foreign_flow: {e}")
        all_ok = False
    
    # Test bandarmology
    result = analyze_bandarmology(ticker)
    try:
        json.dumps(result)
        print("✅ analyze_bandarmology: OK")
    except Exception as e:
        print(f"❌ analyze_bandarmology: {e}")
        all_ok = False
    
    # Test tape reading
    result = analyze_tape_reading(ticker)
    try:
        json.dumps(result)
        print("✅ analyze_tape_reading: OK")
    except Exception as e:
        print(f"❌ analyze_tape_reading: {e}")
        all_ok = False
    
    return all_ok


if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "BBRI"
    
    print("\n🔍 COMPLETE SMART MONEY ANALYSIS")
    print("=" * 60)
    print("Testing IDX-optimized smart money detection with:")
    print("- Volume-price action analysis (not real foreign flow)")
    print("- Bandarmology with 3-volume regime")
    print("- ARA/ARB detection with tick size support")
    print("- Tape reading for intraday pressure")
    print()
    
    # Test all three analyses
    print_foreign_flow(ticker)
    print_bandarmology(ticker)
    print_tape_reading(ticker)
    
    # Test JSON serialization
    test_json_serialization()
    
    print("=" * 60)
    print("✅ Analysis Complete!")
    print("=" * 60)
