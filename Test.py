import os
from coinbase.rest import RESTClient

API_KEY_NAME = os.environ.get("COINBASE_API_KEY_NAME", "your_api_key_name_here")
API_SECRET_KEY = os.environ.get("COINBASE_API_SECRET", "your_api_secret_key_here")
client = RESTClient(api_key=API_KEY_NAME, api_secret=API_SECRET_KEY)

print("🔍 Scanning raw Coinbase API account fields...")
response = client.get_accounts(limit=250)
data = response.to_dict() if hasattr(response, "to_dict") else response
accounts = data.get("accounts", [])

for acc in accounts:
    currency = acc.get("currency")
    available = acc.get("available_balance", {}).get("value")
    hold = acc.get("hold", {}).get("value")
    
    # Only print accounts that aren't completely empty
    if float(available or 0) > 0 or float(hold or 0) > 0:
        print(f"Ticker: {currency:<7} | Available: {available:<10} | Hold: {hold}")
