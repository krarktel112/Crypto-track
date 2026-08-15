import os
import time
from coinbase.rest import RESTClient

# Initialize the secure client
API_KEY_NAME = os.environ.get("COINBASE_API_KEY_NAME", "your_api_key_name_here")
API_SECRET_KEY = os.environ.get("COINBASE_API_SECRET", "your_api_secret_key_here")

client = RESTClient(api_key=API_KEY_NAME, api_secret=API_SECRET_KEY)

# --- 1. SET YOUR INITIAL PURCHASE QUANTITIES ONLY ---
# Type what you originally bought/staked (excluding any generated rewards).
BASE_PURCHASE_AMOUNTS = {
    "BTC": 0.00000000, 
    "ETH": 0.00105000, 
    "SOL": 0.06276400  
}

# --- 2. SET YOUR FIXED HARDCODED AVERAGE BUY COSTS ---
AVERAGE_PRICES = {
    "BTC": 64200.00,  # Example: Change to your exact average entry cost
    "ETH": 3120.00,   # Example: Change to your exact average entry cost
    "SOL": 145.50     # Example: Change to your exact average entry cost
}

def fetch_auto_staking_rewards():
    """Scans all historical transaction events to tally up every reward payout."""
    rewards_tally = {"ETH": 0.0, "SOL": 0.0, "BTC": 0.0}
    
    try:
        # Pull accounts to find internal wallet IDs needed for ledger checks
        response = client.get_accounts(limit=250)
        data = response.to_dict() if hasattr(response, "to_dict") else (response if isinstance(response, dict) else {})
        accounts = data.get("accounts", [])
        
        for account in accounts:
            ticker = str(account.get("currency", "")).upper().strip()
            
            if ticker in rewards_tally:
                account_id = account.get("uuid")
                if not account_id:
                    continue
                
                # Pull the ledger records for this specific coin container
                try:
                    tx_response = client.get_account_transactions(account_uuid=account_id, limit=100)
                    tx_data = tx_response.to_dict() if hasattr(tx_response, "to_dict") else tx_response
                    transactions = tx_data.get("transactions", [])
                    
                    for tx in transactions:
                        # Identify staking reward items handed out by Coinbase
                        tx_type = tx.get("type", "").upper()
                        if tx_type in ["STAKING_REWARD", "STAKING_PAYOUT", "REWARD"]:
                            amount_block = tx.get("amount", {})
                            try:
                                reward_value = float(amount_block.get("value", "0"))
                                rewards_tally[ticker] += reward_value
                            except (ValueError, TypeError):
                                pass
                except Exception:
                    pass # Silently proceed if individual ledger channel times out
                    
    except Exception as e:
        print(f"⚠️ Warning: Could not auto-fetch rewards history ({e}). Using baseline data.")
        
    return rewards_tally

def get_live_price(ticker):
    """Fetches real-time spot market pricing directly from Coinbase SDK."""
    try:
        product = client.get_product(product_id=f"{ticker}-USD")
        if hasattr(product, "price"):
            return float(product.price)
        elif isinstance(product, dict) and "price" in product:
            return float(product["price"])
    except Exception:
        pass
    return 0.0

def main_verification_loop():
    """Aggregates purchases, checks transaction registries for rewards, and pairs with costs."""
    print("🔄 Connecting to Coinbase API and analyzing ledger for rewards...")
    
    # 1. Fetch any liquid trading balances (like your fluid BTC fraction)
    try:
        response = client.get_accounts(limit=250)
        data = response.to_dict() if hasattr(response, "to_dict") else (response if isinstance(response, dict) else {})
        accounts = data.get("accounts", [])
    except Exception as e:
        print(f"❌ API Failure: {e}")
        return

    # 2. Get the auto-updating sum of your earned staking rewards
    live_rewards = fetch_auto_staking_rewards()

    print("\n==========================================================")
    print("             VERIFIED REAL-TIME TOTAL BALANCES            ")
    print("==========================================================")

    total_portfolio_value = 0.0
    total_portfolio_cost = 0.0

    for token in sorted(BASE_PURCHASE_AMOUNTS.keys()):
        # Calculate Total Balance = (Initial Staked/Bought) + (API Liquid Balance) + (Auto-Discovered Rewards)
        initial_base = BASE_PURCHASE_AMOUTNS = BASE_PURCHASE_AMOUNTS.get(token, 0.0)
        earned_rewards = live_rewards.get(token, 0.0)
        
        # Read liquid wallet fraction if any exists on the exchange layer
        liquid_exchange_wallet = 0.0
        for acc in accounts:
            if str(acc.get("currency", "")).upper().strip() == token:
                try:
                    liquid_exchange_wallet = float(acc.get("available_balance", {}).get("value", "0"))
                except:
                    pass
        
        # Consolidate everything together dynamically
        if token == "BTC":
            # For BTC, rely on what the exchange reads since it isn't staking
            total_balance = liquid_exchange_wallet if liquid_exchange_wallet > 0 else initial_base
        else:
            total_balance = initial_base + earned_rewards + liquid_exchange_wallet

        avg_buy = AVERAGE_PRICES.get(token, 0.0)
        live_spot_price = get_live_price(token)
        
        # Financial Computations
        current_value = total_balance * live_spot_price
        initial_cost = initial_base * avg_buy  # Cost stays tied to your actual fiat out-of-pocket
        net_profit = current_value - initial_cost
        
        total_portfolio_value += current_value
        total_portfolio_cost += initial_cost

        # Display matrix formatting
        print(f"• {token:<4} Total Amount: {total_balance:.8f}")
        if earned_rewards > 0:
            print(f"       [Includes +{earned_rewards:.8f} {token} Auto-Updated Rewards]")
            
        print(f"       Avg Buy Price: ${avg_buy:,.2f} | Live Spot: ${live_spot_price:,.2f}")
        print(f"       Holding Value: ${current_value:,.2f}")
        
        if avg_buy > 0:
            status = "🟢 PROFIT" if net_profit >= 0 else "🔴 LOSS"
            print(f"       Net Return:    ${net_profit:+,.2f} [{status}]")
        print("-" * 50)

    print("==========================================================")
    print(f"TOTAL PORTFOLIO VALUE: ${total_portfolio_value:,.2f}")
    if total_portfolio_cost > 0:
        total_return = total_portfolio_value - total_portfolio_cost
        summary_status = "🟢 NET GAIN" if total_return >= 0 else "🔴 NET LOSS"
        print(f"TOTAL NET PERFORMANCE: ${total_return:+,.2f} [{summary_status}]")
    print("==========================================================\n")

if __name__ == "__main__":
    while True:
        try:
            main_verification_loop()
            time.sleep(30)
            os.system('clear')
        except:
            print("Error, retrying")
            time.sleep(30)
            os.system('clear')
