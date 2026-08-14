import os
from coinbase.rest import RESTClient

API_KEY_NAME = os.environ.get("COINBASE_API_KEY_NAME", "your_api_key_name_here")
API_SECRET_KEY = os.environ.get("COINBASE_API_SECRET", "your_api_secret_key_here")

client = RESTClient(api_key=API_KEY_NAME, api_secret=API_SECRET_KEY)

def raw_debug_check():
    print("Sending request... (Fetching raw rows matching ETH or SOL)")
    try:
        # Fetch the max allowed accounts in one call to bypass pagination issues
        response = client.get_accounts(limit=250)
        
        if hasattr(response, "to_dict"):
            data = response.to_dict()
        else:
            data = response if isinstance(response, dict) else {}

        accounts = data.get("accounts", [])
        
        print("\n=== RAW COINBASE DATA DETECTED ===")
        found_any = False
        
        for account in accounts:
            ticker = str(account.get("currency", "")).upper()
            
            # Print EVERYTHING that starts with ETH or SOL (like ETH, SOL, ETH2, usdc-sol, etc.)
            if "ETH" in ticker or "SOL" in ticker:
                found_any = True
                
                # Print exactly what Coinbase is feeding the script
                available = account.get("available_balance", {})
                hold = account.get("hold", {})
                
                print(f"Asset Name: {ticker}")
                print(f"  -> Type/Name: {account.get('name')}")
                print(f"  -> Available Value: {available.get('value')}")
                print(f"  -> Hold/Pending Value: {hold.get('value')}")
                print(f"  -> Portfolio ID: {account.get('portfolio_id')}")
                print("-" * 40)
                
        if not found_any:
            print("❌ The API did not return any rows containing 'ETH' or 'SOL' strings at all.")

    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    raw_debug_check()
