import time
from curl_cffi import requests

# Configuration
API_KEY = "ZFEQKMEBZ6T7NERFNZHEFM8NIE46HRHZ9A"
BASE_URL = "https://etherscan.io"

def trace_tokens(wallet_address, depth=1, max_depth=3):
    """
    Traces outbound ERC-20 token movements and attempts to classify destination addresses.
    """
    if depth > max_depth:
        return

    print(f"\n" + "  " * (depth - 1) + f"└── [Layer {depth}] Scanning Tokens for: {wallet_address}")
    
    # Targeting token transfer logs specifically
    params = {
        "chainid": "1", 
        "module": "account",
        "action": "tokentx", # Switched from standard txlist to track USDT, USDC, etc.
        "address": wallet_address,
        "startblock": 0,
        "endblock": 99999999,
        "page": 1,
        "offset": 30, 
        "sort": "desc",
        "apikey": API_KEY
    }
    
    try:
        response = requests.get(BASE_URL, params=params, impersonate="chrome")
        
        if response.status_code != 200:
            print("  " * depth + f"⚠️ Server Refusal. Status Code: {response.status_code}")
            return
            
        data = response.json()
        
        if data.get("status") == "1" and data.get("message") == "OK":
            tx_list = data["result"]
            found_outbound = False
            processed_txs = set() # Avoid repeating identical transactions
            
            for tx in tx_list:
                # Isolating outbound transfers where funds left the target wallet
                if tx["from"].lower() == wallet_address.lower():
                    tx_hash = tx["hash"]
                    if tx_hash in processed_txs:
                        continue
                    processed_txs.add(tx_hash)
                    
                    found_outbound = True
                    token_symbol = tx.get("tokenSymbol", "UNKNOWN")
                    token_name = tx.get("tokenName", "Unknown Token")
                    decimals = int(tx.get("tokenDecimal", 18))
                    
                    # Convert raw big integer to standard decimal format
                    token_value = float(tx["value"]) / 10**decimals
                    next_wallet = tx["to"]
                    tx_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(int(tx["timeStamp"])))
                    
                    # Identify the type of destination address
                    platform_info = analyze_address_metadata(next_wallet)
                    
                    print("  " * depth + f"➡️ Sent {token_value:.2f} {token_symbol} ({token_name})")
                    print("  " * depth + f"   To: {next_wallet}")
                    print("  " * depth + f"   Destination Profile: {platform_info}")
                    print("  " * depth + f"   Tx: {tx_hash}")
                    
                    time.sleep(1.0)
                    
                    # If it hit an exchange, the trail stops on public ledgers; do not recurse deeper
                    if "CEX" not in platform_info:
                        trace_tokens(next_wallet, depth + 1, max_depth)
            
            if not found_outbound:
                print("  " * depth + "🛑 No outgoing token transfers detected from this address.")
                
        else:
            print("  " * depth + f"⚠️ Etherscan Message: {data.get('result', 'No transaction data matching criteria.')}")
            
    except Exception as e:
        print("  " * depth + f"❌ Tracker execution error: {e}")

def analyze_address_metadata(address):
    """
    Checks the wallet address against a baseline index of known entities.
    Because Etherscan guards its proprietary labels behind a paid API tier,
    common high-volume exchange and protocol hubs are hardcoded here for identification.
    """
    addr_lower = address.lower()
    
    # Common exchange entry points, bridges, and protocols
    known_entities = {
        "0x28c6c06298d514db089934071355e5743bf21d60": "🏢 CEX | Exchange Wallet | Binance",
        "0xf977814e90da44bfa03b6295a0616a897441acec": "🏢 CEX | Cold Storage | Binance",
        "0x4775744cda72bc13506f36421d824d55b005b5aa": "🏢 CEX | Hot Wallet | Coinbase",
        "0x71660c4db2e1eed855c378eac01ec4cf3673c683": "🏢 CEX | Exchange Wallet | Kraken",
        "0x68b3462838f4c16db3461120e8b625845242475e": "🔄 DEX | Smart Contract | Uniswap Router",
        "0x3fc91a3afd903de2709942e6b9c690ee4313f88f": "🔄 DEX | Universal Router | Uniswap",
        "0x0000000000007f150bd6f54c40a34d7c3d5e9f56": "🔄 DEX | Aggregator Pool | CoW Protocol",
        "0x40ec5b33b54e0e8a33a975908c5ba1c14e5bbbdf": "🌉 BRIDGE | Cross-Chain Gateway | Polygon Bridge",
    }
    
    if addr_lower in known_entities:
        return known_entities[addr_lower]
        
    # Heuristics for standard smart contracts vs. personal user wallets
    # Note: Scammers rely heavily on unlabelled intermediary addresses (EOAs)
    return "👤 USER WALLET (EOA) or New Untagged Intermediary Address"

# Running analysis starting from the known pooling wallet
pooling_wallet = "0x220fe14412bca438b3dbc5078e04f802f8f098e7"
print("Launching Token Trace with Entity Attribution...")
trace_tokens(pooling_wallet, depth=1, max_depth=3)
