import os
from coinbase.rest import RESTClient

# Initialize the secure client
API_KEY_NAME = os.environ.get("COINBASE_API_KEY_NAME", "your_api_key_name_here")
API_SECRET_KEY = os.environ.get("COINBASE_API_SECRET", "your_api_secret_key_here")

client = RESTClient(api_key=API_KEY_NAME, api_secret=API_SECRET_KEY)

def verify_all_paginated_balances():
    """Loops through all paginated Coinbase pages to find missing active balances."""
    print("Fetching complete account history across all pages...")
    
    all_accounts = []
    cursor = None
    has_next = True
    page_count = 1

    try:
        # Loop through all pages provided by the API
        while has_next:
            # Query accounts, passing a pagination cursor if we have one
            if cursor:
                response = client.get_accounts(cursor=cursor)
            else:
                response = client.get_accounts()

            # Safeguard/Force object mapping to dictionary
            if hasattr(response, "to_dict"):
                data = response.to_dict()
            elif isinstance(response, dict):
                data = response
            else:
                data = {}

            # Append the current page's accounts to our master list
            page_accounts = data.get("accounts", [])
            all_accounts.extend(page_accounts)

            # Check for additional pages
            has_next = data.get("has_next", False)
            cursor = data.get("cursor", None)
            page_count += 1

        print(f"Scanned {len(all_accounts)} internal wallets across {page_count-1} API pages.\n")
        print("=== ACTIVE TOKEN BALANCES ===")
        found_tokens = False

        for account in all_accounts:
            ticker = account.get("currency")
            
            # Unpack the specific available balance key
            bal_block = account.get("available_balance", {})
            balance_str = bal_block.get("value", "0") if isinstance(bal_block, dict) else "0"
                
            try:
                balance = float(balance_str)
            except (ValueError, TypeError):
                balance = 0.0
                
            # Filter layout: Strictly tokens holding actual assets
            if balance > 0.0 and ticker:
                print(f"• {str(ticker).upper()}: {balance:.8f}")
                found_tokens = True
                
        if not found_tokens:
            print("No active token balances uncovered.")
            
    except Exception as e:
        print(f"❌ API Error: {e}")

if __name__ == "__main__":
    verify_all_paginated_balances()
