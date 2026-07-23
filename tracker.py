import csv
import time
import requests

# Configuration
API_KEY = "ZFEQKMEBZ6T7NERFNZHEFM8NIE46HRHZ9A"
BASE_URL = "https://etherscan.io"
CSV_FILENAME = "crypto_trace_report.csv"

def initialize_csv():
    """Creates the CSV file and writes the header row."""
    fields = [
        "Layer", 
        "Source Wallet", 
        "Direction", 
        "Destination Wallet", 
        "Amount Moved", 
        "Asset Token", 
        "Transaction Date (UTC)", 
        "Transaction Hash"
    ]
    with open(CSV_FILENAME, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(fields)
    print(f"📊 Created empty spreadsheet: {CSV_FILENAME}")

def log_to_csv(row_data):
    """Appends a discovered transaction row to the spreadsheet."""
    with open(CSV_FILENAME, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(row_data)

def trace_and_export(wallet_address, layer=1, action_type="tokentx"):
    """
    Queries Etherscan, processes outbound value transfers, and saves them to a CSV.
    Safely toggles between ERC-20 tokens (USDT/USDC) and raw Ethereum (ETH).
    """
    print(f"\n📡 [Layer {layer}] Scanning {action_type.upper()} history for: {wallet_address}")
    
    params = {
        "module": "account",
        "action": action_type,
        "address": wallet_address,
        "startblock": "0",
        "endblock": "99999999", # Up to today's current blocks in 2026
        "page": "1",
        "offset": "30",          # Captures up to 30 paths per wallet hop
        "sort": "desc",
        "apikey": API_KEY
    }
    
    # Fix network routing context: Ignore broken local network proxies causing the NameResolutionError
    session = requests.Session()
    session.trust_env = False 
    
    try:
        response = session.get(BASE_URL, params=params, timeout=20)
        
        if response.status_code != 200:
            print(f"❌ Connection Blocked by Server (HTTP {response.status_code})")
            return []
            
        data = response.json()
        
        if data.get("status") == "1" and data.get("message") == "OK":
            transactions = data.get("result", [])
            outbound_hops = []
            outbound_count = 0
            
            for tx in transactions:
                # Isolate money leaving the wallet we are investigating
                if tx.get("from", "").lower() == wallet_address.lower():
                    # Parse token metadata vs standard Ethereum chains
                    symbol = tx.get("tokenSymbol", "ETH" if action_type == "txlist" else "TOKEN")
                    decimals = int(tx.get("tokenDecimal", 18)) if action_type == "tokentx" else 18
                    value = float(tx.get("value", 0)) / 10**decimals
                    destination = tx.get("to", "")
                    tx_hash = tx.get("hash", "")
                    
                    # Convert UNIX block timestamp to human-readable date format
                    tx_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(int(tx.get("timeStamp", 0))))
                    
                    if value > 0 and destination:
                        outbound_count += 1
                        outbound_hops.append(destination)
                        
                        # Write directly into the spreadsheet row template
                        row = [layer, wallet_address, "OUTBOUND", destination, f"{value:.4f}", symbol, tx_time, tx_hash]
                        log_to_csv(row)
                        
                        print(f"   ➡️ Exported: {value:.2f} {symbol} sent to {destination[:10]}...")
            
            print(f"✅ Finished wallet. Logged {outbound_count} outbound transfers to CSV.")
            return list(set(outbound_hops)) # Returns unique next hops to follow
            
        else:
            # Automatic fallback: If ERC-20 token logs are completely empty, search raw ETH paths instead
            if action_type == "tokentx":
                print("ℹ️ No token activity found. Automatically scanning for standard ETH transfers...")
                return trace_and_export(wallet_address, layer, action_type="txlist")
                
            print(f"ℹ️ Ledger Status: {data.get('result', 'No transaction activity recorded.')}")
            return []
            
    except Exception as e:
        print(f"❌ Network or Processing Fault: {e}")
        return []

# Execution Entry Point
if __name__ == "__main__":
    initialize_csv()
    
    # Target addresses provided from your MetaSleuth and Cash App traces
    initial_wallets = [
        "0x675150eeec3cffa64d92d5d6ab5ab4cd4ef70633",
        "0xb591b2a6382025d8a39c2ad8dfd4a88d422e4f14",
        "0x220fe14412bca438b3dbc5078e04f802f8f098e7"
    ]
    
    # Layer 1 Scan
    layer_2_targets = []
    for wallet in initial_wallets:
        next_hops = trace_and_export(wallet, layer=1)
        layer_2_targets.extend(next_hops)
        time.sleep(1.0) # Maintain free-tier API rate limits safely
        
    # Layer 2 Scan (Automatically follows the money one step deeper if targets exist)
    layer_2_targets = list(set(layer_2_targets)) # Clear duplicates
    if layer_2_targets:
        print(f"\n==================================================")
        print(f"🔄 LAYER 2: Automatically tracing next-generation hops...")
        print(f"==================================================")
        for wallet in layer_2_targets[:10]: # Safe limit to top 10 secondary wallets to prevent massive bloat
            trace_and_export(wallet, layer=2)
            time.sleep(1.0)

    print(f"\n🏁 Process Complete. Open '{CSV_FILENAME}' to inspect your forensic ledger data timeline.")
