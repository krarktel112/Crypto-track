import os
import json

def initialize_grid():
    state_file = "portfolio_state.json"
    
    if not os.path.exists(state_file):
        return

    with open(state_file, "r") as f:
        state = json.load(f)
        
    gt = state.get("grid_trading", {})
    
    # If open orders are already configured, stay silent in the background
    if "open_orders" in gt and len(gt["open_orders"]) > 0:
        return

    pair = gt.get("active_pair", "BTC-USD")
    lower = gt.get("lower_bound", 55000.0)
    upper = gt.get("upper_bound", 75000.0)
    levels = gt.get("grid_levels", 10)
    amount_usd = gt.get("amount_per_grid_usd", 25.0)
    
    # Calculate arithmetic grid price steps
    step = (upper - lower) / levels
    grid_prices = [lower + (i * step) for i in range(levels + 1)]
    
    print(f"🤖 --- Grid Trading Engine Initialized [{pair}] ---")
    print(f"  • Range: ${lower:,.2f} ➡️ ${upper:,.2f} ({levels} intervals)")
    print(f"  • Capital Allocation: ${amount_usd:,.2f} per grid level")
    
    # Placeholder current price for layout mapping
    mock_current_price = 65000.0 
    
    open_orders = []
    for idx, price in enumerate(grid_prices):
        action = "BUY" if price < mock_current_price else "SELL"
        open_orders.append({
            "level": idx + 1,
            "price": round(price, 2),
            "action": action,
            "amount_usd": amount_usd,
            "status": "OPEN"
        })
        
    # Sync open orders back into the state file schema
    gt["open_orders"] = open_orders
    state["grid_trading"] = gt
    
    with open(state_file, "w") as f:
        json.dump(state, f, indent=4)
        
    print("✅ Grid architecture computed and locked into portfolio_state.json!\n")

if __name__ == "__main__":
    initialize_grid()
