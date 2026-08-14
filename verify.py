import os
from coinbase.rest import RESTClient

# Initialize the secure client
API_KEY_NAME = os.environ.get("COINBASE_API_KEY_NAME", "your_api_key_name_here")
API_SECRET_KEY = os.environ.get("COINBASE_API_SECRET", "your_api_secret_key_here")

client = RESTClient(api_key=API_KEY_NAME, api_secret=API_SECRET_KEY)

def verify_live_balances():
    """Queries Coinbase to print all active token amounts."""
    print("Connecting to Coinbase API...")
    try:
        response = client.get_accounts()
        
        # Extract accounts list depending on SDK response structure
        if hasattr(response, "accounts"):
            accounts = response.accounts
        elif isinstance(response, dict):
            accounts = response.get("accounts", [])
        else:
            accounts = []
            
        if not accounts:
            print("❌ Connection successful, but no account data found.")
            return

        print("\n=== VERIFIED LIVE BALANCES ===")
        found_tokens = False

        for account in accounts:
            # Handle dictionary vs object format
            if isinstance(account, dict):
                ticker = account.get("currency")
                bal_block = account.get("available_balance", {})
                balance_str = bal_block.get("value", "0") if isinstance(bal_block, dict) else getattr(bal_block, "value", "0")
            else:
                ticker = getattr(account, "currency", None)
                bal_block = getattr(account, "available_balance", None)
                balance_str = getattr(bal_block, "value", "0") if bal_block else "0"
                
            try:
                balance = float(balance_str)
            except (ValueError, TypeError):
                balance = 0.0
                
            # Print any account that holds a balance
            if balance > 0 and ticker:
                print(f"Token: {str(ticker).upper():<6} | Amount: {balance:.8f}")
                found_tokens = True
                
        if not found_tokens:
            print("ℹ️ API connected, but all token balances are currently 0.0")
            
    except Exception as e:
        print(f"❌ API Error: Could not fetch live balances. Details: {e}")

if __name__ == "__main__":
    verify_live_balances()
