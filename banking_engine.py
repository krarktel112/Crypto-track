import json

def process_banking_logic():
    state_file = "portfolio_state.json"
    
    if not json.loads(open(state_file, "r").read() if open(state_file, "r") else "{}"):
        return

    with open(state_file, "r") as f:
        state = json.load(f)
        
    bank_cfg = state.get("banking_and_cashout", {})
    target_reserve = bank_cfg.get("target_cash_reserve_usd", 100.0)
    withdraw_threshold = bank_cfg.get("auto_withdraw_threshold_usd", 500.0)
    accumulated_profit = bank_cfg.get("accumulated_profit_usd", 0.0)
    payout_id = bank_cfg.get("payout_method_id", "ACH_LINKED_BANK_ID_OR_NAME")
    
    # Only print and execute output when the threshold is genuinely met
    if accumulated_profit >= withdraw_threshold:
        payout_amount = accumulated_profit - target_reserve
        if payout_amount > 0:
            print("\n🏦 --- Banking & Cash-Out Automation ---")
            print(f"  • Target Cash Reserve: ${target_reserve:,.2f}")
            print(f"  • Auto-Withdrawal Threshold: ${withdraw_threshold:,.2f}")
            print(f"  • Current Accumulated Profit: ${accumulated_profit:,.2f}")
            print(f"  • Payout Destination ID: {payout_id}")
            print(f"\n🚨 THRESHOLD MET (${withdraw_threshold:,.2f})!")
            print(f"  👉 Initiating ACH transfer of ${payout_amount:,.2f} to {payout_id}...")
            print(f"  👉 Retaining baseline cash reserve of ${target_reserve:,.2f} in ecosystem.")
            
            # Reset accumulated profit after withdrawal trigger
            bank_cfg["accumulated_profit_usd"] = target_reserve
            
            # Sync updated state back into JSON
            state["banking_and_cashout"] = bank_cfg
            with open(state_file, "w") as f:
                json.dump(state, f, indent=4)
                
            print("✅ Banking state updated and synced successfully!\n")
    
    # If below threshold, it stays completely silent in the background.

if __name__ == "__main__":
    process_banking_logic()
