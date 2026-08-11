import os
import time
import requests
from coinbase.rest import RESTClient

# Initialize the secure client
API_KEY_NAME = os.environ.get("COINBASE_API_KEY_NAME", "your_api_key_name_here")
API_SECRET_KEY = os.environ.get("COINBASE_API_SECRET", "your_api_secret_key_here")

client = RESTClient(api_key=API_KEY_NAME, api_secret=API_SECRET_KEY)

# --- COINBASE ADVANCED FEE CONFIGURATION ---
FEE_TICKERS = {
    "MAKER": 0.0040,  
    "TAKER": 0.0060   
}
ACTIVE_FEE_MODE = "TAKER"

# --- COST BASIS CONFIGURATION ---
PORTFOLIO_1_COSTS = {
    "BTC": 0.0,
    "ETH": 0.0,      
    "SOL": 4.8       
}

PORTFOLIO_2_COSTS = {
    "BTC": 0.0,
    "ETH": 0.0,      
    "SOL": 0.0       
}

def fetch_live_balances():
    """Queries Coinbase to pull actual active balances dynamically, handling object model properties."""
    live_portfolio = {}
    try:
        response = client.get_accounts()
        
        # Modern SDK returns an object with an 'accounts' attribute containing a list
        if hasattr(response, "accounts"):
            accounts = response.accounts
        elif isinstance(response, dict):
            accounts = response.get("accounts", [])
        else:
            accounts = []
            
        for account in accounts:
            # Handle both object attributes and legacy dictionary keys safely
            if hasattr(account, "currency"):
                ticker = account.currency
                balance_str = account.available_balance.value if hasattr(account, "available_balance") else "0"
            else:
                ticker = account.get("currency")
                balance_str = account.get("available_balance", {}).get("value", "0")
                
            try:
                balance = float(balance_str)
            except (ValueError, TypeError):
                balance = 0.0
                
            # Filter out empty entries and internal non-tradable strings
            if balance > 0 and ticker and len(str(ticker)) <= 4:
                live_portfolio[str(ticker).upper()] = balance
                
    except Exception as e:
        print(f"Warning: Could not fetch live balances ({e}). Using fallback data.")
        
    return live_portfolio


def get_sdk_price(ticker):
    """Uses the official Coinbase SDK to get clean prices with a reliable public fallback."""
    clean_ticker = str(ticker).strip().upper()
    product_id = f"{clean_ticker}-USD"
    
    # 1. Primary Attempt: Use the SDK Client
    try:
        product = client.get_product(product_id=product_id)
        if isinstance(product, dict) and "price" in product:
            return float(product["price"])
        elif hasattr(product, "price"):
            return float(product.price)
    except Exception:
        pass  # Fall through to fallback if SDK fails or authentication is strictly read-only
        
    # 2. Secondary Attempt: Safe Public REST Endpoint (No API Key Required)
    try:
        url = f"https://coinbase.com{clean_ticker}-USD/spot"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return float(res.json()['data']['amount'])
    except Exception:
        pass
        
    return 0.0


def calculate_asset_profit(ticker, amount, price, cost_basis_dict):
    value = amount * price
    cost = cost_basis_dict.get(ticker, 0.0)
    fee_factor = FEE_TICKERS.get(ACTIVE_FEE_MODE, 0.0060)
    profit = value - cost - (value * fee_factor)
    
    if ticker == "BTC":
        profit = 0.0
        
    status_label = "🟢 PROFIT" if profit >= 0 else "🔴 LOSS"
    return value, profit, status_label

def display_portfolio(portfolio, rewards):
    print(f"----------------------------------------------------------\n")
    print(f"Fee Calculation Mode: Coinbase Advanced [{ACTIVE_FEE_MODE} ({FEE_TICKERS[ACTIVE_FEE_MODE]*100:.2f}%)]\n")
    
    # --- PORTFOLIO 1: MAIN WALLET ---
    print("=== PRIMARY PORTFOLIO ===")
    total_value = 0.0
    total_profit = 0.0
    for ticker, amount in portfolio.items():
        price = get_sdk_price(ticker)
        if price == 0.0:
            continue
            
        value, profit, status = calculate_asset_profit(ticker, amount, price, PORTFOLIO_1_COSTS)
        total_value += value
        total_profit += profit
        
        print(f"{ticker}: ${price:.2f} (Own {amount} {ticker} | Value: ${value:.2f} | Profit: ${profit:.2f} [{status}])")
    
    portfolio_status = "🟢 NET PROFIT" if total_profit >= 0 else "🔴 NET LOSS"
    print(f"Total Portfolio Value: ${total_value:.2f} | Total Profit: ${total_profit:.2f} [{portfolio_status}]\n")
    
    # --- PORTFOLIO 2: STAKING & REWARDS ---
    print("=== STAKING & REWARDS PORTFOLIO ===")
    total_rewards_value = 0.0
    total_rewards_profit = 0.0
    for ticker, amount in rewards.items():
        price = get_sdk_price(ticker)
        if price == 0.0:
            continue
            
        value, profit, status = calculate_asset_profit(ticker, amount, price, PORTFOLIO_2_COSTS)
        total_rewards_value += value
        total_rewards_profit += profit
        
        print(f"{ticker}: ${price:.2f} (Own {amount} {ticker} | Value: ${value:.2f} | Profit: ${profit:.2f} [{status}])")
        
    rewards_status = "🟢 NET PROFIT" if total_rewards_profit >= 0 else "🔴 NET LOSS"
    print(f"Total Reward Value: ${total_rewards_value:.2f} | Reward Profit: ${total_rewards_profit:.2f} [{rewards_status}]\n")
    print(f"----------------------------------------------------------\n")

def conversion_matrix(recover_amount, label):
    ethereum = get_sdk_price("ETH")
    solana = get_sdk_price("SOL")
    
    if ethereum == 0.0 or solana == 0.0:
        print(f"[{label}] Conversion matrix paused: Missing asset prices.")
        return
        
    value_eth = (((recover_amount / ethereum) / 0.04307645) * 0.15)
    value_sol = (((recover_amount / solana) / 0.051702936) * 0.01)
    
    x = recover_amount / ethereum 
    y = recover_amount / solana
    
    print(f"[{label}] Ethereum {round(x, 5)}: ${value_eth:.2f}")
    print(f"[{label}] Solana {round(y, 5)}: ${value_sol:.2f}")

def main():
    while True:
        try:
            live_portfolio = fetch_live_balances()
            if not live_portfolio:
                live_portfolio = {
                    'ETH': 0.00000364,
                    'SOL': 0.051808054
                }
                
            staking_rewards = {
                'ETH': 0.00000364,
                'SOL': 0.000350292
            }
            
            display_portfolio(live_portfolio, staking_rewards)
            conversion_matrix(10216.3, "Recovery Tier 1")
            conversion_matrix(6008.08, "Recovery Tier 2")
            
        except Exception as e:
            print(f"Error in execution loop: {e}")
            
        time.sleep(30)
        os.system('cls' if os.name == 'nt' else 'clear')

if __name__ == "__main__":
    main()
