import time
from curl_cffi import requests

# Configuration
API_KEY = "ZFEQKMEBZ6T7NERFNZHEFM8NIE46HRHZ9A"
# Updated to Etherscan v2 endpoint for better performance
BASE_URL = "https://api.etherscan.io/v2/api"

def trace_wallet(wallet_address, depth=1, max_depth=3):
    """
    Recursively traces outbound ETH transfers using advanced browser impersonation.
    """
    if depth > max_depth:
        return

    print(f"\n" + "  " * (depth - 1) + f"└── [Layer {depth}] Scanning Outbound from: {wallet_address}")
    
    # Required parameters for Etherscan account transaction logs
    params = {
        "chainid": "1", # 1 = Ethereum Mainnet
        "module": "account",
        "action": "txlist",
        "address": wallet_address,
        "startblock": 0,
        "endblock": 99999999,
        "page": 1,
        "offset": 25, 
        "sort": "desc",
        "apikey": API_KEY
    }
    
    try:
        # impersonate="chrome" forces the network layer to completely mimic a real Google Chrome browser
        response = requests.get(BASE_URL, params=params, impersonate="chrome")
        
        if response.status_code != 200:
            print("  " * depth + f"⚠️ Server rejected connection. Status Code: {response.status_code}")
            return
            
        data = response.json()
        
        if data.get("status") == "1" and data.get("message") == "OK":
            tx_list = data["result"]
            found_outbound = False
            
            for tx in tx_list:
                # Check for outbound transfers with active value
                if tx["from"].lower() == wallet_address.lower() and float(tx["value"]) > 0:
                    found_outbound = True
                    ether_value = float(tx["value"]) / 10**18
                    next_wallet = tx["to"]
                    tx_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(int(tx["timeStamp"])))
                    
                    print("  " * depth + f"➡️ Sent {ether_value:.4f} ETH to {next_wallet} ({tx_time})")
                    print("  " * depth + f"   Tx Hash: {tx['hash']}")
                    
                    # Restrict speed to avoid hitting Etherscan free tier rate limits (5 calls/sec)
                    time.sleep(1.0) 
                    
                    # Core logic: jump into the next wallet address
                    trace_wallet(next_wallet, depth + 1, max_depth)
            
            if not found_outbound:
                print("  " * depth + "🛑 No outgoing value transfers found from this address.")
                
        else:
            print("  " * depth + f"⚠️ Etherscan Message: {data.get('result', 'No result payload')}")
            
    except Exception as e:
        print("  " * depth + f"❌ Execution error: {e}")

# Target pooling wallet discovered via MetaSleuth
pooling_wallet = "0x220fe14412bca438b3dbc5078e04f802f8f098e7"
print("Starting secure trace on pooling wallet...")
trace_wallet(pooling_wallet, depth=1, max_depth=300)
