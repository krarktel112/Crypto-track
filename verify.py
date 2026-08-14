import os
from coinbase.rest import RESTClient

# Initialize the secure client
API_KEY_NAME = os.environ.get("COINBASE_API_KEY_NAME", "your_api_key_name_here")
API_SECRET_KEY = os.environ.get("COINBASE_API_SECRET", "your_api_secret_key_here")

client = RESTClient(api_key=API_KEY_NAME, api_secret=API_SECRET_KEY)

def verify_live_balances():
    """Queries Coinbase and outputs ONLY tokens with active balances."""
    try:
        response = client.get_accounts()
        
        # Force the SDK response object into a clean dictionary structure
        if hasattr(response, "to_dict"):
            data = response.to_dict()
        elif isinstance(response, dict):
            data = response
        else:
            data = {}

        accounts = data.get("accounts", [])
        
        print("=== ACTIVE TOKEN BALANCES ===")
        found_tokens = False

        for account in accounts:
            ticker = account.get("currency")
            
            # Extract balance value string from nested block
            bal_block = account.get("available_balance", {})
            balance_str = bal_block.get("value", "0") if isinstance(bal_block, dict) else "0"
                
            try:
                balance = float(balance_str)
            except (ValueError, TypeError):
                balance = 0.0
                
            # STRICT FILTER: Only print if token balance is actively greater than zero
            if balance > 0.0 and ticker:
                print(f"• {str(ticker).upper()}: {balance:.8f}")
                found_tokens = True
                
        if not found_tokens:
            print("No active token balances found.")
            
    except Exception as e:
        print(f"❌ API Error: {e}")

if __name__ == "__main__":
    verify_live_balances()
