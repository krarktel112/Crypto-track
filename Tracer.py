import requests
import time

# Configuration
API_KEY = "ZFEQKMEBZ6T7NERFNZHEFM8NIE46HRHZ9A"
BASE_URL = "https://etherscan.io"

# Headers to prevent 403 Forbidden / Cloudflare blocks
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def trace_wallet(wallet_address, depth=1, max_depth=3):
    """
    Recursively traces outbound ETH transfers up to a specified maximum depth.
    """
    if depth > max_depth:
        return

    print(f"\n" + "  " * (depth - 1) + f"└── [Layer {depth}] Scanning Outbound from: {wallet_address}")
    
    params = {
        "module": "account",
        "action": "txlist",
        "address": wallet_address,
        "startblock": 0,
        "endblock": 99999999,
        "page": 1,
        "offset": 20, # Reduced size for cleaner output
        "sort": "desc",
        "apikey": API_KEY
    }
    
    try:
        # Added headers parameter to fix the JSON parsing error
        response = requests.get(BASE_URL, params=params, headers=HEADERS)
        
        # Check if the server actually returned a 200 OK status
        if response.status_code != 200:
            print("  " * depth + f"⚠️ Server returned HTTP Status {response.status_code}")
            return
            
        data = response.json()
        
        if data["status"] == "1" and data["message"] == "OK":
            tx_list = data["result"]
            found_outbound = False
            
            for tx in tx_list:
                # Track outbound transfers with actual value
                if tx["from"].lower() == wallet_address.lower() and float(tx["value"]) > 0:
                    found_outbound = True
                    ether_value = float(tx["value"]) / 10**18
                    next_wallet = tx["to"]
                    tx_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(int(tx["timeStamp"])))
                    
                    print("  " * depth + f"➡️ Sent {ether_value:.4f} ETH to {next_wallet} ({tx_time})")
                    
                    # Prevent instant rate limiting by pausing briefly
                    time.sleep(0.2) 
                    
                    # Recursively trace the next hop
                    trace_wallet(next_wallet, depth + 1, max_depth)
            
            if not found_outbound:
                print("  " * depth + "🛑 No outgoing value transfers found from this address.")
                
        else:
            print("  " * depth + f"⚠️ Etherscan API Notice: {data.get('result', 'No data returned')}")
            
    except requests.exceptions.JSONDecodeError:
        print("  " * depth + "❌ Failed to parse response. Etherscan might be blocking the request.")
    except Exception as e:
        print("  " * depth + f"❌ Request error: {e}")

# Start the trace from the pooling wallet you identified
pooling_wallet = "0x220fe14412bca438b3dbc5078e04f802f8f098e7"
print(f"Starting trace from pooling wallet...")
trace_wallet(pooling_wallet, depth=1, max_depth=3)
