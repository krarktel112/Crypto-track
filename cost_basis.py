import json

def calculate_true_averages():
    state_file = "portfolio_state.json"
    
    with open(state_file, "r") as f:
        state = json.load(f)
        
    # Support both nested "assets" key and flat top-level token keys
    assets_data = state.get("assets", {})
    if not assets_data:
        assets_data = {k: v for k, v in state.items() if isinstance(v, dict) and "balance" in v}

    print("📊 --- True Cost-Basis & Asset Summary ---")
    
    for token, details in assets_data.items():
        exchange_balance = details.get("balance", 0.0)
        exchange_avg_buy = details.get("avg_buy", 0.0)
        
        ext = details.get("external_purchases", {})
        ext_units = ext.get("total_units", 0.0)
        ext_usd = ext.get("total_usd_spent", 0.0)
        
        exchange_usd_spent = exchange_balance * exchange_avg_buy
        total_units = exchange_balance + ext_units
        total_usd_spent = exchange_usd_spent + ext_usd
        
        if total_units > 0:
            true_avg_buy = total_usd_spent / total_units
        else:
            true_avg_buy = 0.0
            
        print(f"\nAsset: {token}")
        print(f"  • Exchange Balance: {exchange_balance:,.8f} @ ${exchange_avg_buy:,.2f} avg")
        print(f"  • External Purchases: {ext_units:,.8f} units (${ext_usd:,.2f} spent)")
        print(f"  • Total Holdings: {total_units:,.8f} {token}")
        print(f"  • True Weighted Avg Buy: ${true_avg_buy:,.2f}")

if __name__ == "__main__":
    calculate_true_averages()
