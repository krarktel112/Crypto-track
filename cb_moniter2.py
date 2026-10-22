import json
import time

STATE_FILE = "portfolio_state.json"

def load_state():
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)

def run_cost_basis():
    state = load_state()
    print("\n📊 --- 1. True Cost-Basis & Asset Summary ---")
    for token, details in state.get("assets", {}).items():
        ex_bal = details.get("balance", 0.0)
        ex_avg = details.get("avg_buy", 0.0)
        ext = details.get("external_purchases", {})
        ext_units = ext.get("total_units", 0.0)
        ext_usd = ext.get("total_usd_spent", 0.0)
        
        ex_usd_spent = ex_bal * ex_avg
        total_units = ex_bal + ext_units
        total_usd_spent = ex_usd_spent + ext_usd
        
        true_avg = (total_usd_spent / total_units) if total_units > 0 else 0.0
        
        print(f"Asset: {token}")
        print(f"  • Total Holdings: {total_units:,.8f} {token}")
        print(f"  • True Weighted Avg Buy: ${true_avg:,.2f}")

def run_grid_engine():
    state = load_state()
    gt = state.get("grid_trading", {})
    pair = gt.get("active_pair", "BTC-USD")
    lower = gt.get("lower_bound", 55000.0)
    upper = gt.get("upper_bound", 75000.0)
    levels = gt.get("grid_levels", 10)
    amount_usd = gt.get("amount_per_grid_usd", 25.0)
    
    step = (upper - lower) / levels
    grid_prices = [lower + (i * step) for i in range(levels + 1)]
    
    print(f"\n🤖 --- 2. Grid Trading Engine: {pair} ---")
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
    gt["open_orders"] = open_orders
    state["grid_trading"] = gt
    save_state(state)
    print(f"  • Computed {len(open_orders)} grid levels successfully and synced to state.")

def run_banking_engine():
    state = load_state()
    bank_cfg = state.get("banking_and_cashout", {})
