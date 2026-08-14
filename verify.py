import os
from coinbase.rest import RESTClient

# Initialize the secure client
API_KEY_NAME = os.environ.get("COINBASE_API_KEY_NAME", "your_api_key_name_here")
API_SECRET_KEY = os.environ.get("COINBASE_API_SECRET", "your_api_secret_key_here")

client = RESTClient(api_key=API_KEY_NAME, api_secret=API_SECRET_KEY)

# Define the exact tickers you want to watch
TARGET_TOKENS = {"BTC", "ETH", "SOL"}

def verify_target_balances():
    """Queries Coinbase specifically searching for requested target assets."""
    print("Searching Coinbase accounts for BTC, ETH, and SOL...")
    
    all_accounts = []
    cursor = None
    has_next = True

    try:
        # Loop pagination while maximizing the results fetched per request
        while has_next:
            if cursor:
                response = client.get_accounts(cursor=cursor, limit=250)
            else:
                response = client.get_accounts(limit=250)

            # Unify structure to a dict
            if hasattr(response, "to_dict"):
                data = response.to_dict()
            elif isinstance(response, dict):
                data = response
            else:
                data = {}

            all_accounts.extend(data.get("accounts", []))
            has_next = data.get("has_next", False)
            cursor = data.get("cursor", None)

        print("\n=== VERIFIED TARGET BALANCES ===")
        found_matches = {ticker: 0.0 for ticker in TARGET_TOKENS}

        for account in all_accounts:
            ticker = str(account.get("currency", "")).upper().strip()
            
            # Match strictly against your target coins
            if ticker in TARGET_TOKENS:
                bal_block = account.get("available_balance", {})
                balance_str = bal_block.get("value", "0") if isinstance(bal_block, dict) else "0"
                
                try:
                    balance = float(balance_str)
                except (ValueError, TypeError):
                    balance = 0.0
                
                # Save the highest balance found for this token (filters out legacy duplicate rows)
                if balance > found_matches[ticker]:
                    found_matches[ticker] = balance

        # Output the clean filtered metrics
        for token in sorted(TARGET_TOKENS):
            print(f"• {token}: {found_matches[token]:.8f}")
            
    except Exception as e:
        print(f"❌ API Error: {e}")

if __name__ == "__main__":
    verify_target_balances()
