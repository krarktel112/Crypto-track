import time
import random
import requests

# Configuration
API_KEY = "ZFEQKMEBZ6T7NERFNZHEFM8NIE46HRHZ9A"
# Using standard v1 endpoint for stable free-tier API parameters
BASE_URL = "https://etherscan.io"

def analyze_address_metadata(address):
    """
    Identifies common exchange hubs or smart contract routers.
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
    return known_entities.get(addr_lower, "👤 UNTAGGED WALLET / TRANSIT HOP")

def fetch_transactions_with_retry(params, max_retries=3):
    """
    Handles standard HTTP requests with error-resilient retry logic.
    """
    delay = 2.0
    for attempt in range(max_retries):
        try:
            # Removed custom headers entirely; Etherscan API expects clean, direct hits
            response = requests.get(BASE_URL, params=params, timeout=15)
            
            if response.status_code == 200:
                return response.json()
            
            if response.status_code in [403, 429]:
                # Dynamic backoff delay if the API starts throttling your IP
                sleep_time = delay + random.uniform(0.5, 1.5)
                print(f"      ⚠️ Throttled (Status {response.status_code}). Retrying in {sleep_time:.1f}s...")
                time.sleep(sleep_time)
                delay *= 2
            else:
                print(f"      ⚠️ HTTP Server Error: {response.status_code}")
                return None
        except Exception as e:
            print(f"      ⚠️ Request execution failed: {e}")
            time.sleep(delay)
    return None

def trace_chain_to_present(start_wallets, max_layers=3):
    """
    Performs layer-by-layer tracking across target wallets up to the current date.
    """
    current_layer_wallets = set(w.lower() for w in start_wallets)
    visited_wallets = set(current_layer_wallets)
    processed_txs = set()

    for layer in range(1, max_layers + 1):
        if not current_layer_wallets:
            print("\n🏁 Trace completed: No more active outbound paths discovered.")
            break
            
        print(f"\n================ [LAYER {layer} RUNNING] ================")
        next_layer_wallets = set()

        for wallet in list(current_layer_wallets):
            print(f"\n🔍 Investigating Ledger Activity: {wallet}")
            
            # Formulating API parameters for tracking ERC-20 token histories (USDT/USDC)
            params = {
                "module": "account",
                "action": "tokentx",
                "address": wallet,
                "startblock": "0",
                "endblock": "99999999", # Forces scan up to today's current blocks
                "page": "1",
                "offset": "20",          # Focuses on the 20 most recent transfers
                "sort": "desc",
                "apikey": API_KEY
            }

            data = fetch_transactions_with_retry(params)
            if not data:
                continue

            if data.get("status") == "1" and data.get("message") == "OK":
                tx_list = data.get("result", [])
                outbound_found = False

                for tx in tx_list:
                    # Filter for outbound flows
                    if tx.get("from", "").lower() == wallet.lower():
                        tx_hash = tx.get("hash")
                        if tx_hash in processed_txs:
                            continue
                        processed_txs.add(tx_hash)
                        
                        destination = tx.get("to", "").lower()
                        symbol = tx.get("tokenSymbol", "TOKEN")
                        decimals = int(tx.get("tokenDecimal", 18))
                        value = float(tx.get("value", 0)) / 10**decimals
                        tx_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(int(tx.get("timeStamp", 0))))

                        if value > 0 and destination:
                            outbound_found = True
                            profile = analyze_address_metadata(destination)
                            
                            print(f"      ➡️ Sent {value:.2f} {symbol}")
                            print(f"         Date: {tx_time}")
                            print(f"         To: {destination}")
                            print(f"         Entity: {profile}")
                            print(f"         Hash: {tx_hash}\n")

                            if "🏢 CEX" in profile:
                                print(f"         🛑 Trail hit Exchange Ledger. On-chain auditing ends here.")
                                continue

                            if destination not in visited_wallets:
                                visited_wallets.add(destination)
                                next_layer_wallets.add(destination)
                
                if not outbound_found:
                    print("      🛑 No outbound value movement recorded.")
            else:
                # Fallback check for raw ETH if token logs return empty or clean
                params["action"] = "txlist"
                eth_data = fetch_transactions_with_retry(params)
                if eth_data and eth_data.get("status") == "1":
                    print("      ℹ️ Found standard ETH movement instead of ERC-20 tokens.")
                else:
                    print(f"      ℹ️ Etherscan Info: {data.get('result', 'No active records.')}")

            # Enforces API tier preservation spacing
            time.sleep(0.5)

        current_layer_wallets = next_layer_wallets

# Execution Root
initial_wallets = [
    "0x675150eeec3cffa64d92d5d6ab5ab4cd4ef70633",
    "0xb591b2a6382025d8a39c2ad8dfd4a88d422e4f14",
    "0x220fe14412bca438b3dbc5078e04f802f8f098e7"
]

trace_chain_to_present(initial_wallets, max_layers=3)
