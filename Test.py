import os
from coinbase.rest import RESTClient

# Initialize the secure client
API_KEY_NAME = os.environ.get("COINBASE_API_KEY_NAME", "your_api_key_name_here")
API_SECRET_KEY = os.environ.get("COINBASE_API_SECRET", "your_api_secret_key_here")

client = RESTClient(api_key=API_KEY_NAME, api_secret=API_SECRET_KEY)

def run_diagnostic_audit():
    print("🔄 Connecting to Coinbase ledger structures...")
    try:
        # Use get_accounts to list details
        response = client.get_accounts(limit=250)
        data = response.to_dict() if hasattr(response, "to_dict") else (response if isinstance(response, dict) else {})
        accounts = data.get("accounts", [])
        
        sol_account_found = False
        for acc in accounts:
            ticker = str(acc.get("currency", "")).upper().strip()
            if ticker == "SOL":
                sol_account_found = True
                account_uuid = acc.get("uuid")
                print(f"✅ Found SOL Account Ledger. UUID: {account_uuid}\n")
                
                print("==========================================================")
                print("             RAW SOL TRANSACTION TYPE AUDIT               ")
                print("==========================================================")
                
                # Dynamic check for transaction tracking fallback method in modern SDK
                try:
                    # Fetch ledger updates using transactions fallback endpoint
                    tx_response = client.get_account(account_uuid=account_uuid)
                    tx_data = tx_response.to_dict() if hasattr(tx_response, "to_dict") else tx_response
                    
                    # Print raw metadata to verify configuration keys
                    print("💼 Raw Account Details Parsed Successfully.")
                    print(f"   Available Balance: {tx_data.get('account', {}).get('available_balance', {}).get('value')}")
                    print(f"   Hold Balance:      {tx_data.get('account', {}).get('hold', {}).get('value')}")
                    print("-" * 50)
                    
                except Exception as inner_e:
                    print(f"⚠️ Account detail extraction failed: {inner_e}")
                
                # Check for historical transactions through universal fill mappings
                try:
                    fills_response = client.get_fills(product_id="SOL-USD", limit=50)
                    fills_data = fills_response.to_dict() if hasattr(fills_response, "to_dict") else fills_response
                    fills = fills_data.get("fills", [])
                    
                    if not fills:
                        print("ℹ️  No direct order book fills found. Checking ledger entries...")
                    else:
                        for idx, fill in enumerate(fills, 1):
                            print(f"[{idx}] Trade Entry:")
                            print(f"    🏷️  Type: Trade Fill")
                            print(f"    📊 Size: {fill.get('size')} SOL")
                            print(f"    💵 Price: ${fill.get('price')}")
                            print("-" * 50)
                except Exception as fill_e:
                    print(f"⚠️ Could not pull fills ledger: {fill_e}")

        if not sol_account_found:
            print("❌ SOL wallet ledger structure was not returned by the accounts endpoint.")
            
    except Exception as e:
        print(f"❌ Diagnostic failed with error: {e}")

if __name__ == "__main__":
    run_diagnostic_audit()
