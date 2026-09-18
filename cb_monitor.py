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
    "ETH": 0.00000000, 
    "SOL": 0.113659785
}

# --- 2. SET YOUR FIXED HARDCODED AVERAGE BUY COSTS ---
AVERAGE_PRICES = {
    "BTC": 0.01,  # Example: Change to your exact average entry cost
    "ETH": 0.0,   # Example: Change to your exact average entry cost
    "SOL": 87.37  # Example: Change to your exact average entry cost
}

def fetch_staked_solana_balance():
    """Queries Coinbase's dedicated Earn/Staking API to find hidden staked SOL."""
    try:
        # Calls the specific CDP Earn/Staking endpoint
        response = client.get_staking_balances()
        data = response.to_dict() if hasattr(response, "to_dict") else response
        balances = data.get("balances", [])
        
        for bal in balances:
            # Check for Solana staking allocations
            if str(bal.get("currency", "")).upper().strip() == "SOL":
                return float(bal.get("amount", {}).get("value", "0"))
    except Exception:
        # Fallback if your API key lacks explicit Earn/Staking permissions
        pass
    return 0.0

def fetch_auto_staking_rewards():
    """Scans all historical transaction events to tally up every reward payout."""
    rewards_tally = {"ETH": 0.0, "SOL": 0.0, "BTC": 0.0}
    
    try:
        response = client.get_accounts(limit=250)
        data = response.to_dict() if hasattr(response, "to_dict") else (response if isinstance(response, dict) else {})
        accounts = data.get("accounts", [])
        
        for account in accounts:
            ticker = str(account.get("currency", "")).upper().strip()
            
            if ticker in rewards_tally:
                account_id = account.get("uuid")
                if not account_id:
                    continue
                
                try:
                    tx_response = client.get_account_transactions(account_uuid=account_id, limit=100)
                    tx_data = tx_response.to_dict() if hasattr(tx_response, "to_dict") else tx_response
                    transactions = tx_data.get("transactions", [])
                    
                    for tx in transactions:
                        tx_type = tx.get("type", "").upper()
                        if tx_type in ["STAKING_REWARD", "STAKING_PAYOUT", "REWARD"]:
                            amount_block = tx.get("amount", {})
                            try:
                                reward_value = float(amount_block.get("value", "0"))
                                rewards_tally[ticker] += reward_value
                            except (ValueError, TypeError):
                                pass
                except Exception:
                    pass
                    
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
    
    try:
        response = client.get_accounts(limit=250)
        data = response.to_dict() if hasattr(response, "to_dict") else (response if isinstance(response, dict) else {})
        accounts = data.get("accounts", [])
    except Exception as e:
        print(f"❌ API Failure: {e}")
        return

    live_rewards = fetch_auto_staking_rewards()
    
    # NEW: Fetch your hidden staked Solana balance directly from the Earn ledger
    staked_solana = fetch_staked_solana_balance()

    print("\n==========================================================")
    print("             VERIFIED REAL-TIME TOTAL BALANCES            ")
    print("==========================================================")

    total_portfolio_value = 0.0
    total_portfolio_cost = 0.0

    for token in sorted(BASE_PURCHASE_AMOUNTS.keys()):
        initial_base = BASE_PURCHASE_AMOUNTS.get(token, 0.0)
        earned_rewards = live_rewards.get(token, 0.0)
        
        liquid_exchange_wallet = 0.0
        for acc in accounts:
            currency_ticker = str(acc.get("currency", "")).upper().strip()
            if token in currency_ticker:
                try:
                    available = float(acc.get("available_balance", {}).get("value", "0"))
                    held = float(acc.get("hold", {}).get("value", "0"))
                    liquid_exchange_wallet += (available + held)
                except:
                    pass
        
        # Consolidate balances dynamically
        if token == "BTC":
            total_balance = liquid_exchange_wallet if liquid_exchange_wallet > 0 else initial_base
        elif token == "SOL":
            # For SOL, explicitly add the hidden vault balance found in the Earn API
            total_balance = initial_base + earned_rewards + liquid_exchange_wallet + staked_solana
        else:
            total_balance = initial_base + earned_rewards + liquid_exchange_wallet

        avg_buy = AVERAGE_PRICES.get(token, 0.0)
        live_spot_price = get_live_price(token)
        
        # Financial Computations
        current_value = total_balance * live_spot_price
        initial_cost = initial_base * avg_buy
        net_profit = current_value - initial_cost
        
        total_portfolio_value += current_value
        total_portfolio_cost += initial_cost

        # Display matrix formatting
        print(f"• {token:<4} Total Amount: {total_balance:.8f}")
        if token == "SOL" and staked_solana > 0:
            print(f"       [Detected +{staked_solana:.8f} SOL inside Coinbase Staking Vault]")
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
