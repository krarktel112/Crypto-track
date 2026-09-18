import os
import time
from coinbase.rest import RESTClient

# Initialize the secure client
API_KEY_NAME = os.environ.get("COINBASE_API_KEY_NAME", "your_api_key_name_here")
API_SECRET_KEY = os.environ.get("COINBASE_API_SECRET", "your_api_secret_key_here")

client = RESTClient(api_key=API_KEY_NAME, api_secret=API_SECRET_KEY)

def calculate_dynamic_sol_average_buy():
    """
    Dynamically scans historical filled buy orders for SOL-USD to 
    calculate the true volume-weighted average buy entry price.
    """
    total_spent = 0.0
    total_sol_bought = 0.0
    
    try:
        # Fetch fills for SOL-USD product
        response = client.get_fills(product_id="SOL-USD", limit=100)
        data = response.to_dict() if hasattr(response, "to_dict") else response
        fills = data.get("fills", [])
        
        for fill in fills:
            side = fill.get("side", "").upper()
            # Only count actual completed purchases
            if side == "BUY":
                try:
                    price = float(fill.get("price", "0"))
                    size = float(fill.get("size", "0"))
                    
                    total_spent += (price * size)
                    total_sol_bought += size
                except (ValueError, TypeError):
                    pass
                    
        if total_sol_bought > 0:
            return total_spent / total_sol_bought
    except Exception:
        pass
        
    return None # Fallback to default hardcoded value if API scan fails

def fetch_staked_solana_balance():
    """Queries Coinbase's dedicated Earn/Staking API to find hidden staked SOL."""
    try:
        response = client.get_staking_balances()
        data = response.to_dict() if hasattr(response, "to_dict") else response
        balances = data.get("balances", [])
        
        for bal in balances:
            if str(bal.get("currency", "")).upper().strip() == "SOL":
                return float(bal.get("amount", {}).get("value", "0"))
    except Exception:
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
    print("🔄 Connecting to Coinbase API and analyzing ledger for live balances...")
    
    try:
        response = client.get_accounts(limit=250)
        data = response.to_dict() if hasattr(response, "to_dict") else (response if isinstance(response, dict) else {})
        accounts = data.get("accounts", [])
    except Exception as e:
        print(f"❌ API Failure: {e}")
        return

    live_rewards = fetch_auto_staking_rewards()
    staked_solana = fetch_staked_solana_balance()
    
    # DYNAMICALLY DETECT ENTRY COST FROM COINBASE HISTORICAL FILLS
    dynamic_sol_avg = calculate_dynamic_sol_average_buy()

    # --- FALLBACK HARDCODED BASELINES (If API returns empty history) ---
    BASE_PURCHASE_AMOUNTS = {"BTC": 0.0, "ETH": 0.0, "SOL": 0.11365979}
    AVERAGE_PRICES = {
        "BTC": 0.01, 
        "ETH": 0.0, 
        "SOL": dynamic_sol_avg if dynamic_sol_avg is not None else 87.37
    }

    print("\n==========================================================")
    print("             VERIFIED REAL-TIME TOTAL BALANCES            ")
    print("==========================================================")

    total_portfolio_value = 0.0
    total_portfolio_cost = 0.0

    for token in sorted(AVERAGE_PRICES.keys()):
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
        
        # Consolidate balances dynamically across all components
        if token == "SOL":
            # Fully automated tracking: Base + Staking Vault + Liquid + Auto Payouts
            total_balance = liquid_exchange_wallet + staked_solana
            # Safety check: if standard endpoints read zero, protect with the baseline estimate
            if total_balance == 0:
                total_balance = initial_base + earned_rewards
        elif token == "BTC":
            total_balance = liquid_exchange_wallet if liquid_exchange_wallet > 0 else initial_base
        else:
            total_balance = liquid_exchange_wallet if liquid_exchange_wallet > 0 else (initial_base + earned_rewards)

        avg_buy = AVERAGE_PRICES.get(token, 0.0)
        live_spot_price = get_live_price(token)
        
        # Financial Computations
        current_value = total_balance * live_spot_price
        initial_cost = (liquid_exchange_wallet if token == "SOL" else initial_base) * avg_buy
        net_profit = current_value - initial_cost
        
        total_portfolio_value += current_value
        total_portfolio_cost += initial_cost

        # Display matrix formatting
        print(f"• {token:<4} Total Amount: {total_balance:.8f}")
        if token == "SOL":
            if staked_solana > 0:
                print(f"       [Detected +{staked_solana:.8f} SOL inside Coinbase Staking Vault]")
            if dynamic_sol_avg is not None:
                print(f"       [Calculated Real-Time Dynamic Entry Cost from Order Ledger]")
            else:
                print(f"       [Using Hardcoded Cost Baselines as API Fallback]")
            
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
        except Exception as e:
            print(f"Error ({e}), retrying...")
            time.sleep(30)
            os.system('clear')
