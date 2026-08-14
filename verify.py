import os
from coinbase.rest import RESTClient

# Initialize the secure client
API_KEY_NAME = os.environ.get("COINBASE_API_KEY_NAME", "your_api_key_name_here")
API_SECRET_KEY = os.environ.get("COINBASE_API_SECRET", "your_api_secret_key_here")

client = RESTClient(api_key=API_KEY_NAME, api_secret=API_SECRET_KEY)

# Define your locked staking balances since the Advanced Trade API reports them as 0
STAKED_BALANCES = {
    "ETH": 0.00105000,
    "SOL": 0.06276400
}

def verify_total_balances():
    """Combines live liquid balances with your active staking assets."""
    try:
        # Fetch the available spot trading wallets
        response = client.get_accounts(limit=250)
        
        if hasattr(response, "to_dict"):
            data = response.to_dict()
        else:
            data = response if isinstance(response, dict) else {}

        accounts = data.get("accounts", [])
        
        # Initialize tracking with your staked tokens
        total_holdings = {
            "BTC": 0.0,
            "ETH": STAKED_BALANCES.get("ETH", 0.0),
            "SOL": STAKED_BALANCES.get("SOL", 0.0)
        }

        # Add any remaining fluid liquid balances found on the spot exchange
        for account in accounts:
            ticker = str(account.get("currency", "")).upper().strip()
            
            if ticker in total_holdings:
                bal_block = account.get("available_balance", {})
                balance_str = bal_block.get("value", "0") if isinstance(bal_block, dict) else "0"
                
                try:
                    liquid_value = float(balance_str)
                except (ValueError, TypeError):
                    liquid_value = 0.0
                
                # BTC will be added here; liquid fractions of ETH/SOL will combine with staked amounts
                total_holdings[ticker] += liquid_value

        print("=== VERIFIED TOTAL ACCOUNT BALANCES ===")
        for token in sorted(total_holdings.keys()):
            print(f"• {token}: {total_holdings[token]:.8f}")

    except Exception as e:
        print(f"❌ API Error: {e}")

if __name__ == "__main__":
    verify_total_balances()
