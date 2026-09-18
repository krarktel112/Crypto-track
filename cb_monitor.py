import os
import time
from coinbase.rest import RESTClient

# Initialize the secure client
API_KEY_NAME = os.environ.get("COINBASE_API_KEY_NAME", "your_api_key_name_here")
API_SECRET_KEY = os.environ.get("COINBASE_API_SECRET", "your_api_secret_key_here")

client = RESTClient(api_key=API_KEY_NAME, api_secret=API_SECRET_KEY)

def calculate_ledger_average_buy(accounts_list):
    """
    Scans comprehensive historical ledger activities for SOL to catch retail 
    buys, advanced trades, and external conversions. Calculates true VWAP.
    """
    total_usd_spent = 0.0
    total_sol_acquired = 0.0
    
    try:
        for acc in accounts_list:
            ticker = str(acc.get("currency", "")).upper().strip()
            if ticker == "SOL":
                account_id = acc.get("uuid")
                if not account_id:
                    continue
                
                # Fetch up to 100 recent account transaction events
                tx_response = client.get_account_transactions(account_uuid=account_id, limit=100)
                tx_data = tx_response.to_dict() if hasattr(tx_response, "to_dict") else tx_response
                transactions = tx_data.get("transactions", [])
                
                for tx in transactions:
                    tx_type = tx.get("type", "").upper()
                    # Catch both Advanced Trade fills and Retail App purchases/conversions
                    if tx_type in ["BUY", "TRADE_IN", "TRADE"]:
                        try:
                            # Total amount of SOL acquired in this event
                            sol_amount = float(tx.get("amount", {}).get("value", "0"))
                            
                            # Safely capture what it was worth in USD at execution time
                            native_block = tx.get("native_amount", {})
                            usd_value = abs(float(native_block.get("value", "0")))
                            
                            if sol_amount > 0 and usd_value > 0:
                                total_usd_spent += usd_value
                                total_sol_acquired += sol_amount
                        except (ValueError, TypeError):
                            pass
    except Exception:
        pass
        
    if total_sol_acquired > 0:
        return total_usd_spent / total_sol_acquired
    return None

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

def fetch_auto_staking_rewards(accounts_list):
    """Scans historical transactions to tally rewards across BTC, ETH, and SOL."""
    rewards_tally = {"ETH": 0.0, "SOL": 0.0, "BTC": 0.0}
    
    try:
        for account in accounts_list:
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
                            try:
                                reward_value = float(tx.get("amount", {}).get("value", "0"))
                                rewards_tally[ticker] += reward_value
                            except (ValueError, TypeError):
                                pass
                except Exception:
                    pass
    except Exception:
        pass
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
    """Aggregates purchases, checks ledger histories, and updates matrix metrics."""
    print("🔄 Accessing verified read-only account data structures...")
    
    try:
        response = client.get_accounts(limit=250)
        data = response.to_dict() if hasattr(response, "to_dict") else (response if isinstance(response, dict) else {})
        accounts = data.get("accounts", [])
    except Exception as e:
        print(f"❌ API Failure: {e}")
        return

    live_rewards = fetch_auto_staking_rewards(accounts)
    staked_solana = fetch_staked_solana_balance()
    
    # REPLACED: Now extracts history directly from retail & advanced transaction books
    dynamic_sol_avg = calculate_ledger_average_buy(accounts)

    # --- FALLBACK HARDCODED BASELINES ---
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
        
        # Consolidate balances dynamically
        if token == "SOL":
            total_balance = liquid_exchange_wallet + staked_solana
            if total_balance == 0:
                total_balance = initial_base + earned_rewards
        elif token == "BTC":
            total_balance = liquid_exchange_wallet if liquid_exchange_wallet > 0 else initial_base
        else:
            total_balance = liquid_exchange_wallet if liquid_exchange_wallet > 0 else (initial_base + earned_rewards)

        avg_buy = AVERAGE_PRICES.get(token, 0.0)
        live_spot_price = get_live_price(token)
        
        current_value = total_balance * live_spot_price
        initial_cost = (liquid_exchange_wallet if token == "SOL" else initial_base) * avg_buy
        net_profit = current_value - initial_cost
        
        total_portfolio_value += current_value
        total_portfolio_cost += initial_cost

        print(f"• {token:<4} Total Amount: {total_balance:.8f}")
        if token == "SOL":
            if staked_solana > 0:
                print(f"       [Detected +{staked_solana:.8f} SOL inside Coinbase Staking Vault]")
            if dynamic_sol_avg is not None:
                print(f"       [Calculated Real-Time Dynamic Entry Cost from Account Ledger]")
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
