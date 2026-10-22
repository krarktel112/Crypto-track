import json

def process_banking_logic():
    state_file = "portfolio_state.json"
    
    with open(state_file, "r") as f:
        state = json.load(f)
        
    bank_cfg = state.get("banking_and_cashout", {})
    target_reserve = bank_cfg.get("target_cash_reserve_usd", 100.0)
    withdraw_threshold = bank_cfg.get("auto_withdraw_threshold_usd", 500.0)
    accumulated_profit = bank_cfg.get("accumulated_profit_usd", 0.0)
    payout_id = bank_cfg.get("payout_method_id", "ACH_LINKED_BANK_ID_OR_NAME")
    
    print("🏦 --- Banking & Cash-Out Automation ---")
    print(f"  • Target Cash Reserve: ${target_reserve:,.2f}")
    print(f"  • Auto-Withdrawal Threshold: ${withdraw_threshold:,.2f}")
    print(f"  • Current Accumulated Profit: ${accumulated_profit:,.2f}")
    print(f"  • Payout Destination ID: {payout_id}")
    
    # Simulate adding a new batch of trading profits for demonstration (e.g., $550.00 from closed grid orders)
    simulated_new_profit = 550.00
    accumulated_profit += simulated_new_profit
    print(f"\n💡 [Simulation Event]: Added ${simulated_new_profit:,.2f} in newly realized grid profits.")
    print(f"  • Updated Accumulated Profit Pool: ${accumulated_profit:,.2f}")
    
    if accumulated_profit >= withdraw_threshold:
        payout_amount = accumulated_profit - target_reserve
        if payout_amount > 0:
            print(f"\n🚨 THRESHOLD MET (${withdraw_threshold:,.2f})!")
            print(f"  👉 Initiating ACH transfer of ${payout_amount:,.2f} to {payout_id}...")
            print(f"  👉 Retaining baseline cash reserve of ${target_reserve:,.2f} in ecosystem.")
            
            # Reset accumulated profit after withdrawal trigger (or retain remainder)
            bank_cfg["accumulated_profit_usd"] = target_reserve
        else:
            print("\n⚠️ Profits exceed threshold, but funds do not exceed target reserve buffer yet.")
            bank_cfg["accumulated_profit_usd"] = accumulated_profit
    else:
        print(f"\n⏳ Below withdrawal threshold. Accumulating profits (Needs ${withdraw_threshold - accumulated_profit:,.2f} more to trigger).")
        bank_cfg["accumulated_profit_usd"] = accumulated_profit
        
    # Sync updated state back into JSON
    state["banking_and_cashout"] = bank_cfg
    with open(state_file, "w") as f:
        json.dump(state, f, indent=4)
        
    print("\n✅ Banking state updated and synced successfully!")

if __name__ == "__main__":
    process_banking_logic()
