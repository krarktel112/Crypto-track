import json
import time

def evaluate_market_logic():
    state_file = "portfolio_state.json"
    
    with open(state_file, "r") as f:
        state = json.load(f)
        
    ml = state.get("market_logic", {})
    ma = ml.get("moving_averages", {})
    indicators = ml.get("indicators", {})
    cooldowns = ml.get("cooldowns", {})
    
    print("📈 --- Heuristic Market Analysis & Rotation ---")
    print(f"  • BTC 50 MA: ${ma.get('BTC_50_ma', 0.0):,.2f}")
    print(f"  • BTC 200 MA: ${ma.get('BTC_200_ma', 0.0):,.2f}")
    print(f"  • BTC Dominance: {indicators.get('btc_dominance', 0.0)}%")
    print(f"  • Altseason Trigger Active: {indicators.get('altseason_trigger', False)}")
    
    # Check cool-down status
    last_trade = cooldowns.get("last_trade_timestamp", 0)
    cooldown_secs = cooldowns.get("cooldown_seconds", 300)
    current_time = int(time.time())
    elapsed = current_time - last_trade
    
    print(f"\n⏱️ Cool-down Status Check:")
    if last_trade == 0:
        print("  • No prior trade recorded. Execution window is OPEN.")
    elif elapsed >= cooldown_secs:
        print(f"  • Cool-down period elapsed ({elapsed}s >= {cooldown_secs}s). Ready for execution.")
    else:
        remaining = cooldown_secs - elapsed
        print(f"  • ⏳ Cooldown active! {remaining} seconds remaining before next trade.")
        
    # Simulate a live data update (e.g., updating MAs and dominance from market feeds)
    print("\n💡 [Simulation Event]: Fetching latest market indicators...")
    ma["BTC_50_ma"] = 64250.0
    ma["BTC_200_ma"] = 58100.0
    indicators["btc_dominance"] = 57.5
    
    # Simple heuristic check: if 50 MA > 200 MA, market is in a structural bull trend
    bull_trend = ma["BTC_50_ma"] > ma["BTC_200_ma"]
    print(f"  • Structural Trend (50 MA > 200 MA): {'BULLISH 🟢' if bull_trend else 'BEARISH 🔴'}")
    
    if indicators["btc_dominance"] < 55.0:
        indicators["altseason_trigger"] = True
        print("  • ⚡ BTC Dominance dropped below 55% -> Altseason rotation triggered!")
    else:
        indicators["altseason_trigger"] = False
        print("  • 🛡️ Dominance strong -> Favoring BTC accumulation.")
        
    # Sync back into state
    ml["moving_averages"] = ma
    ml["indicators"] = indicators
    state["market_logic"] = ml
    
    with open(state_file, "w") as f:
        json.dump(state, f, indent=4)
        
    print("\n✅ Market heuristics evaluated and synced to portfolio_state.json!")

if __name__ == "__main__":
    evaluate_market_logic()
