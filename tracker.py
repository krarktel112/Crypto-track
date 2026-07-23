import time
from collections import deque
from curl_cffi import requests

# Configuration
API_KEY = "ZFEQKMEBZ6T7NERFNZHEFM8NIE46HRHZ9A"
BASE_URL = "https://etherscan.io"

def analyze_address_metadata(address):
    """
    Identifies common centralized hubs, exchanges, or smart contracts.
    """
    addr_lower = address.lower()
    known_entities = {
        "0x28c6c06298d514db089934071355e5743bf21d60": "🏢 CEX | Binance Hot Wallet",
        "0xf977814e90da44bfa03b6295a0616a897441acec": "🏢 CEX | Binance Cold Storage",
        "0x4775744cda72bc13506f36421d824d55b005b5aa": "🏢 CEX | Coinbase",
        "0x71660c4db2e1eed855c378eac01ec4cf3673c683": "🏢 CEX | Kraken",
        "0x68b3462838f4c16db3461120e8b625845242475e": "🔄 DEX | Uniswap V3 Router",
        "0x3fc91a3afd903de2709942e6b9c690ee4313f88f": "🔄 DEX | Uniswap Universal Router",
        "0x40ec5b33b54e0e8a33a975908c5ba1c14e5bbbdf": "🌉 BRIDGE | Polygon Bridge Gateway",
    }
    return known_entities.get(addr_lower, "👤 UNTAGGED WALLET / POTENTIAL SCAMMER HOP")

def trace_funds_to_present(start_wallets, max_layers=4):
    """
    Uses a Queue (BFS) to safely track fund hops sequentially up to the current date.
    """
    # Queue stores: (wallet_to_scan, current_layer_depth)
    queue = deque()
    for wallet in start_wallets:
        queue.append((wallet, 1))
    
    # Global tracking sets to prevent infinite bouncing loops
    visited_wallets = set(w.lower() for w in start_wallets)
    processed_tx_hashes = set()

    print(f"🚀 Initializing tracking loop up to current network time...")

    while queue:
        current_wallet, layer = queue.popleft()
        
        if layer > max_layers:
            continue

        print(f"\n[Layer {layer}] 🔍 Scanning Address: {current_wallet}")
        
        params = {
            "chainid": "1",
            "module": "account",
            "action": "tokentx",  # Tracks stablecoins (USDT/USDC). Change to "txlist" for raw ETH.
            "address": current_wallet,
            "startblock": 0,       # Scan from original block creation
            "endblock": 99999999,  # Up to the highest current block today
            "page": 1,
            "offset": 50,          # Pulls up to 50 transfers per hop
            "sort": "desc",        # Starts with most recent transfers
            "apikey": API_KEY
        }

        try:
            response = requests.get(BASE_URL, params=params, impersonate="chrome")
            if response.status_code != 200:
                print(f"      ⚠️ Connection failed (HTTP {response.status_code})")
                continue
                
            data = response.json()
            
            if data.get("status") == "1" and data.get("message") == "OK":
                tx_list = data["result"]
                outbound_found = False
                
                for tx in tx_list:
                    # Isolate outbound token movement originating from this address
                    if tx["from"].lower() == current_wallet.lower():
                        tx_hash = tx["hash"]
                        
                        # Skip if we already saw this transaction route
                        if tx_hash in processed_tx_hashes:
                            continue
                        processed_tx_hashes.add(tx_hash)
                        outbound_found = True
                        
                        next_wallet = tx["to"]
                        token_symbol = tx.get("tokenSymbol", "TOKEN")
                        decimals = int(tx.get("tokenDecimal", 18))
                        value = float(tx["value"]) / 10**decimals
                        tx_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(int(tx["timeStamp"])))
                        
                        # Only follow paths where value actually moved
                        if value > 0:
                            destination_profile = analyze_address_metadata(next_wallet)
                            print(f"      ➡️ Moved: {value:.2f} {token_symbol}")
                            print(f"         Date/Time: {tx_time}")
                            print(f"         Destination: {next_wallet}")
                            print(f"         Profile: {destination_profile}")
                            print(f"         Tx Hash: {tx_hash}\n")
                            
                            # If it hits a CEX exchange, stop tracking this branch (trail goes dark on-chain)
                            if "🏢 CEX" in destination_profile:
                                print(f"         🛑 Funds reached a Centralized Exchange. Freeze point identified.")
                                continue
                                
                            # Queue up the next wallet if it hasn't been scanned yet
                            if next_wallet.lower() not in visited_wallets:
                                visited_wallets.add(next_wallet.lower())
                                queue.append((next_wallet, layer + 1))
                                
                if not outbound_found:
                    print("      🛑 No further outbound movements found. Funds may currently reside here.")
            else:
                print(f"      ℹ️ Etherscan message: {data.get('result', 'No activity found.')}")
                
        except Exception as e:
            print(f"      ❌ Script error scanning wallet: {e}")
            
        # Rate limit safety delay
        time.sleep(1.0)

# Entry point: Put all your known scam targets into the starting queue
initial_targets = [
    "0x675150eeec3cffa64d92d5d6ab5ab4cd4ef70633",
    "0xb591b2a6382025d8a39c2ad8dfd4a88d422e4f14",
    "0x220fe14412bca438b3dbc5078e04f802f8f098e7"
]

trace_funds_to_present(initial_targets, max_layers=4)
