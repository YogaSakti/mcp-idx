#!/usr/bin/env python3
"""
Test Foreign Flow, Bandarmology & Tape Reading Analysis
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.foreign_flow import analyze_foreign_flow, analyze_bandarmology, analyze_tape_reading


def print_foreign_flow(ticker: str):
    """Test foreign flow analysis"""
    print("=" * 60)
    print(f"FOREIGN FLOW ANALYSIS: {ticker}")
    print("=" * 60)
    
    result = analyze_foreign_flow(ticker, period="3mo")
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return
    
    print(f"\n📊 Ticker: {result['ticker']}")
    print(f"📅 Period: {result['analysis_period']}")
    
    print(f"\n💼 FOREIGN OWNERSHIP:")
    own = result['foreign_ownership']
    print(f"   Insiders: {own['insiders_percent']:.2f}%")
    print(f"   Institutions: {own['institutions_percent']:.2f}%")
    print(f"   Float Institutions: {own['float_institutions_percent']:.2f}%")
    print(f"   Number of Institutions: {own['institutions_count']}")
    
    print(f"\n📈 FLOW ANALYSIS:")
    flow = result['flow_analysis']
    print(f"   Trend: {flow['trend']}")
    print(f"   Accumulation Days: {flow['accumulation_days']}")
    print(f"   Distribution Days: {flow['distribution_days']}")
    print(f"   Net Pattern: {flow['net_pattern']}")
    
    print(f"\n📊 VOLUME METRICS:")
    vol = result['volume_metrics']
    print(f"   Average Volume: {vol['average_volume']:,}")
    print(f"   Recent Volume: {vol['recent_volume']:,}")
    print(f"   Trend: {vol['volume_trend_pct']:+.2f}% ({vol['volume_status']})")
    
    print(f"\n💰 SMART MONEY:")
    sm = result['smart_money']
    print(f"   Score: {sm['score']}/100")
    print(f"   Rating: {sm['rating']}")
    print(f"   Confidence: {sm['confidence']}")
    
    print(f"\n💡 INTERPRETATION:")
    interp = result['interpretation']
    print(f"   Ownership Level: {interp['ownership_level']}")
    print(f"   Foreign Interest: {interp['foreign_interest']}")
    print(f"   Pattern: {interp['pattern']}")
    
    print()


def print_bandarmology(ticker: str):
    """Test bandarmology analysis"""
    print("=" * 60)
    print(f"BANDARMOLOGY ANALYSIS: {ticker}")
    print("=" * 60)
    
    result = analyze_bandarmology(ticker, period="3mo")
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return
    
    print(f"\n📊 Ticker: {result['ticker']}")
    print(f"📅 Period: {result['analysis_period']}")
    
    print(f"\n🎯 CURRENT PHASE:")
    phase = result['current_phase']
    print(f"   Phase: {phase['phase']}")
    print(f"   Signal: {phase['signal']}")
    print(f"   Strength: {phase['strength']}/20")
    print(f"   Confidence: {phase['confidence']}")
    
    print(f"\n📊 PHASE SCORES:")
    scores = result['phase_scores']
    print(f"   Accumulation: {scores['accumulation']}")
    print(f"   Markup: {scores['markup']}")
    print(f"   Distribution: {scores['distribution']}")
    print(f"   Markdown: {scores['markdown']}")
    
    print(f"\n💹 PRICE ACTION:")
    price = result['price_action']
    print(f"   Trend: {price['trend_pct']:+.2f}% ({price['trend_direction']})")
    print(f"   Current: {price['current_price']:,.0f}")
    print(f"   MA20: {price['ma20']:,.0f}")
    print(f"   Position: {price['position_vs_ma20']}")
    
    print(f"\n📊 VOLUME ACTION:")
    vol = result['volume_action']
    print(f"   High Volume Days: {vol['high_volume_days']}/20")
    print(f"   Volume Trend: {vol['volume_trend_pct']:+.2f}% ({vol['volume_status']})")
    
    print(f"\n🎲 BANDAR STRENGTH:")
    bandar = result['bandar_strength']
    print(f"   Score: {bandar['score']:.2f}%")
    print(f"   Rating: {bandar['rating']}")
    print(f"   Active: {'YES' if bandar['active'] else 'NO'}")
    
    print(f"\n💡 RECOMMENDATION:")
    rec = result['recommendation']
    print(f"   Action: {rec['action']}")
    print(f"   Reason: {rec['reason']}")
    print(f"   Risk Level: {rec['risk_level']}")
    
    print()


def print_tape_reading(ticker: str):
    """Test tape reading analysis"""
    print("=" * 60)
    print(f"TAPE READING ANALYSIS: {ticker}")
    print("=" * 60)
    
    result = analyze_tape_reading(ticker, period="5d")
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return
    
    print(f"\n📊 Ticker: {result['ticker']}")
    print(f"📅 Period: {result['analysis_period']}")
    
    print(f"\n💪 CURRENT PRESSURE:")
    press = result['current_pressure']
    print(f"   Pressure: {press['pressure']}")
    print(f"   Buying Bars: {press['buying_bars']}")
    print(f"   Selling Bars: {press['selling_bars']}")
    print(f"   Absorption Bars: {press['absorption_bars']}")
    
    print(f"\n🌊 ORDER FLOW:")
    flow = result['order_flow']
    print(f"   Flow Type: {flow['flow_type']}")
    print(f"   Last Bar Volume Ratio: {flow['last_bar_volume_ratio']:.2f}x")
    print(f"   Last Bar Change: {flow['last_bar_change_pct']:+.2f}%")
    
    print(f"\n📊 LAST BAR DETAILS:")
    bar = result['last_bar_details']
    print(f"   Open: {bar['open']:,.0f}")
    print(f"   High: {bar['high']:,.0f}")
    print(f"   Low: {bar['low']:,.0f}")
    print(f"   Close: {bar['close']:,.0f}")
    print(f"   Volume: {bar['volume']:,}")
    print(f"   Spread: {bar['spread_pct']:.2f}%")
    print(f"   Body: {bar['body_size']:.2f}")
    print(f"   Upper Wick: {bar['upper_wick']:.2f}")
    print(f"   Lower Wick: {bar['lower_wick']:.2f}")
    
    print(f"\n💡 INTERPRETATION:")
    interp = result['interpretation']
    print(f"   Dominant Force: {interp['dominant_force']}")
    print(f"   Market Sentiment: {interp['market_sentiment']}")
    print(f"   Immediate Action: {interp['immediate_action']}")
    
    print()


if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "BBRI"
    
    print("\n🔍 COMPLETE SMART MONEY ANALYSIS\n")
    
    # Test all three analyses
    print_foreign_flow(ticker)
    print_bandarmology(ticker)
    print_tape_reading(ticker)
    
    print("=" * 60)
    print("✅ Analysis Complete!")
    print("=" * 60)
