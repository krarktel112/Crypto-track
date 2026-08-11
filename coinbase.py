import os
from coinbase.advanced.client import CoinbaseAdvancedClient

# 1. Initialize the client with your CDP API Key details
# It is safest to load these from environment variables
API_KEY_NAME = os.environ.get("COINBASE_API_KEY_NAME", "your_api_key_name_here")
API_SECRET_KEY = os.environ.get("COINBASE_API_SECRET", "your_api_secret_key_here")

client = CoinbaseAdvancedClient(api_key=API_KEY_NAME, api_secret=API_SECRET_KEY)

def monitor_wallet():
    print("Fetching wallet balances...\n")
    try:
        # 2. Retrieve all accounts in your portfolio
        response = client.get_accounts()
        accounts = response.get("accounts", [])
        
        # 3. Parse and display non-zero balances
        has_balances = False
        for account in accounts:
            currency = account.get("currency")
            # Get the available balance string and convert to float
            balance_str = account.get("available_balance", {}).get("value", "0")
            balance = float(balance_str)
            
            if balance > 0:
                has_balances = True
                print(f"🪙 Asset: {currency:<6} | 💰 Balance: {balance:<12}")
                
        if not has_balances:
            print("No active crypto balances found in this portfolio.")
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    monitor_wallet()
