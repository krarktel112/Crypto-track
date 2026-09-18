import os
from coinbase.rest import RESTClient

# Ensure your environment variables are configured before running
API_KEY_NAME = os.environ.get("COINBASE_API_KEY_NAME", "your_api_key_name_here")
API_SECRET_KEY = os.environ.get("COINBASE_API_SECRET", "your_api_secret_key_here")

client = RESTClient(api_key=API_KEY_NAME, api_secret=API_SECRET_KEY)

try:
    # Query Coinbase to read key settings
    response = client.get_api_key_permissions()
    data = response.to_dict() if hasattr(response, "to_dict") else response
    
    print("\n==========================================================")
    print("             COINBASE API PERMISSION AUDIT                ")
    print("==========================================================")
    print(f"👁️  Can View Balances/History:  {data.get('can_view', False)}")
    print(f"📊 Can Execute Trades:         {data.get('can_trade', False)}")
    print(f"💸 Can Transfer Funds:         {data.get('can_transfer', False)}")
    print(f"💼 Portfolio Target UUID:      {data.get('portfolio_uuid', 'N/A')}")
    print("==========================================================\n")
    
    if not data.get('can_view', False):
        print("❌ CRITICAL: Your API key lacks 'View' permissions. The ledger will fail to load.")
    else:
        print("✅ SUCCESS: Key possesses active read capabilities.")
        
except Exception as e:
    print(f"❌ Failed to reach permission endpoint: {e}")
