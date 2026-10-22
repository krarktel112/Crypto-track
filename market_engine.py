import json
import time

def evaluate_market_logic(verbose=False):
    state_file = "portfolio_state.json"
    
    with open(state_file, "r") as f:
        state = json.load(f)
        
    ml = state.get("market_logic", {})
    ma = ml.get("moving_averages", {})
    indicators = ml.get("indicators", {})
    cooldowns = ml.get("cooldowns", {})
    
    if verbose:
        print("📈 --- Heuristic Market Analysis & Rotation ---")
        print(f"  • BTC 50 MA: ${ma.get('BTC_50_ma', 0.0):,.2f}")
        print(f"  • BTC 200 MA: ${ma.get('BTC_200_ma', 0.0):,.2f}")
        print(f"  • BTC Dominance: {indicators.get('btc_dominance', 0.0)}%")
    
    # Check cool-down status silently
    last_trade = cooldowns.get("last_trade_timestamp", 0)
    cooldown_secs = cooldowns.get("cooldown_seconds", 300)
    current_time = int(time.time())
    elapsed = current_time - last_trade
    
    # Example simulated updates
    ma["BTC_50_ma"] = 64250.0
    ma["BTC_200_ma"] = 58100.0
    indicators["btc_dominance"] = 57.5
    
    bull_trend = ma["BTC_50_ma"] > ma["BTC_200_ma"]
    
    if indicators["btc_dominance"] < 55.0:
        indicators["altseason_trigger"] = True
        print("\n⚡ [Market Alert]: BTC Dominance dropped below 55% -> Altseason rotation triggered!")
    else:
        indicators["altseason_trigger"] = False
        
    # Sync back into state
    ml["moving_averages"] = ma
    ml["indicators"] = indicators
    state["market_logic"] = ml
    
    with open(state_file, "w") as f:
        json.dump(state, f, indent=4)

if __name__ == "__main__":
    evaluate_market_logic(verbose=True)
