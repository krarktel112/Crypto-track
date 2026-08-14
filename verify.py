import os
import json
from coinbase.rest import RESTClient

# Initialize the secure client
API_KEY_NAME = os.environ.get("COINBASE_API_KEY_NAME", "your_api_key_name_here")
API_SECRET_KEY = os.environ.get("COINBASE_API_SECRET", "your_api_secret_key_here")

client = RESTClient(api_key=API_KEY_NAME, api_secret=API_SECRET_KEY)

def verify_live_balances():
    """Queries Coinbase and forces object dictionary parsing to uncover hidden balances."""
    print("Connecting to Coinbase API...")
    try:
        # Fetch accounts data
        response = client.get_accounts()
        
        # Force the SDK object into a clean Python dictionary structure
        if hasattr(response, "to_dict"):
            data = response.to_dict()
        elif isinstance(response, dict):
            data = response
        else:
            data = {}

        accounts = data.get("accounts", [])
        
        if not accounts:
            print("❌ Connection successful, but the accounts array is empty.")
            return

        print("\n=== VERIFIED LIVE BALANCES ===")
        found_tokens = False

        for account in accounts:
            # Extract fields directly from the dictionary data mapping
            ticker = account.get("currency")
            
            # Coinbase Advanced Trade maps available balance under 'available_balance' -> 'value'
            bal_block = account.get("available_balance", {})
            balance_str = bal_block.get("value", "0") if isinstance(bal_block, dict) else "0"
                
            try:
                balance = float(balance_str)
            except (ValueError, TypeError):
                balance = 0.0
                
            # Show any asset matching your wallet coins
            if balance > 0 and ticker:
                print(f"Token: {str(ticker).upper():<6} | Amount: {balance:.8f}")
                found_tokens = True
                
        if not found_tokens:
            print("ℹ️ API connected, but processed balances returned 0.0")
            print("💡 Debug: Double check if your API key permissions include 'wallet:accounts:read'.")
            
    except Exception as e:
        print(f"❌ API Error: Could not fetch live balances. Details: {e}")

if __name__ == "__main__":
    verify_live_balances()
