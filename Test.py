import os
from coinbase.rest import RESTClient

# Initialize the secure client
API_KEY_NAME = os.environ.get("COINBASE_API_KEY_NAME", "your_api_key_name_here")
API_SECRET_KEY = os.environ.get("COINBASE_API_SECRET", "your_api_secret_key_here")

client = RESTClient(api_key=API_KEY_NAME, api_secret=API_SECRET_KEY)

def run_diagnostic_audit():
    print("🔄 Connecting to Coinbase ledger structures...")
    try:
        response = client.get_accounts(limit=250)
        data = response.to_dict() if hasattr(response, "to_dict") else (response if isinstance(response, dict) else {})
        accounts = data.get("accounts", [])
        
        sol_account_found = False
        for acc in accounts:
            ticker = str(acc.get("currency", "")).upper().strip()
            if ticker == "SOL":
                sol_account_found = True
                account_id = acc.get("uuid")
                print(f"✅ Found SOL Account Ledger. UUID: {account_id}\n")
                print("==========================================================")
                print("             RAW SOL TRANSACTION TYPE AUDIT               ")
                print("==========================================================")
                
                # Fetch recent ledger items
                tx_response = client.get_account_transactions(account_uuid=account_id, limit=100)
                tx_data = tx_response.to_dict() if hasattr(tx_response, "to_dict") else tx_response
                transactions = tx_data.get("transactions", [])
                
                if not transactions:
                    print("⚠️  No transaction history records returned in this ledger window.")
                    return
                
                for idx, tx in enumerate(transactions, 1):
                    tx_id = tx.get("id", "N/A")
                    raw_type = tx.get("type", "UNKNOWN")
                    
                    # Capture quantities
                    amount_val = tx.get("amount", {}).get("value", "0.0")
                    native_val = tx.get("native_amount", {}).get("value", "0.0")
                    native_curr = tx.get("native_amount", {}).get("currency", "USD")
                    
                    print(f"[{idx}] TX ID: {tx_id}")
                    print(f"    🏷️  EXACT RAW TYPE STRING: '{raw_type}'")
                    print(f"    📊 Amount: {amount_val} SOL")
                    print(f"    💵 Native Value: {native_val} {native_curr}")
                    print("-" * 50)
                    
        if not sol_account_found:
            print("❌ SOL wallet ledger structure was not returned by the accounts endpoint.")
            
    except Exception as e:
        print(f"❌ Diagnostic failed with error: {e}")

if __name__ == "__main__":
    run_diagnostic_audit()
