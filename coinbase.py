import os
import time
import requests
from coinbase.advanced.client import CoinbaseAdvancedClient

# Initialize the secure client using your CDP API key details
API_KEY_NAME = os.environ.get("COINBASE_API_KEY_NAME", "your_api_key_name_here")
API_SECRET_KEY = os.environ.get("COINBASE_API_SECRET", "your_api_secret_key_here")

client = CoinbaseAdvancedClient(api_key=API_KEY_NAME, api_secret=API_SECRET_KEY)

# --- COINBASE ADVANCED FEE CONFIGURATION ---
# Base volume tier ($0-$10k) spot trading fees: Maker = 0.40%, Taker = 0.60%
FEE_TICKERS = {
    "MAKER": 0.0040,  # 0.40% for limit orders resting on the book
    "TAKER": 0.0060   # 0.60% for market orders filled instantly (default fallback)
}
ACTIVE_FEE_MODE = "TAKER"  # Change to "MAKER" if you primarily use post-only limit orders

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
    live_portfolio = {}
    try:
        response = client.get_accounts()
        accounts = response.get("accounts", [])
        for account in accounts:
            ticker = account.get("currency")
            balance_str = account.get("available_balance", {}).get("value", "0")
            balance = float(balance_str)
            if balance > 0:
                live_portfolio[ticker] = balance
    except Exception as e:
        print(f"Warning: Could not fetch live data from Coinbase API ({e}). Using fallback data.")
    return live_portfolio

def get_crypto_price(ticker):
    url = f'https://coinbase.com{ticker}-USD/spot'
    response = requests.get(url)
    data = response.json()
    return float(data['data']['amount'])

def calculate_asset_profit(ticker, amount, price, cost_basis_dict):
    """Calculates asset valuation and profit margins using true Coinbase Advanced fee configurations."""
    value = amount * price
    cost = cost_basis_dict.get(ticker, 0.0)
    
    # Extract exact percentage factor based on your trading style selection
    fee_factor = FEE_TICKERS.get(ACTIVE_FEE_MODE, 0.0060)
    
    # Profit = Current Valuation - Your Initial Investment Capital - Realized Trading Fee
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
        try:
            price = get_crypto_price(ticker)
        except Exception:
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
        try:
            price = get_crypto_price(ticker)
        except Exception:
            continue
            
        value, profit, status = calculate_asset_profit(ticker, amount, price, PORTFOLIO_2_COSTS)
        total_rewards_value += value
        total_rewards_profit += profit
        
        print(f"{ticker}: ${price:.2f} (Own {amount} {ticker} | Value: ${value:.2f} | Profit: ${profit:.2f} [{status}])")
        
    rewards_status = "🟢 NET PROFIT" if total_rewards_profit >= 0 else "🔴 NET LOSS"
    print(f"Total Reward Value: ${total_rewards_value:.2f} | Reward Profit: ${total_rewards_profit:.2f} [{rewards_status}]\n")
    print(f"----------------------------------------------------------\n")

def conversion_matrix(recover_amount, label):
    ethereum = get_crypto_price("ETH")
    solana = get_crypto_price("SOL")
    
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
            print(f"Error, retrying. Details: {e}")
            
        time.sleep(30)
        os.system('cls' if os.name == 'nt' else 'clear')

if __name__ == "__main__":
    main()
