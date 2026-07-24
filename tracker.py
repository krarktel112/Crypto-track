import time
import json
import os
import pandas as pd
from datetime import datetime
from curl_cffi import requests

# Configuration
API_KEY = "ZFEQKMEBZ6T7NERFNZHEFM8NIE46HRHZ9A"
BASE_URL = "https://api.etherscan.io/v2/api"

# Known entities for CEX vs DEX classification
# (Expand this dictionary with more contract addresses as needed)
KNOWN_ENTITIES = {
    # Centralized Exchanges (CEX) Deposit / Hot Wallets
    "0x28c6c06298d514db089934071355e5ba621b4d23": {"name": "Binance 14", "type": "CEX"},
    "0xdfd5293d8e347dfe59e90efd55b2956a1343963d": {"name": "Binance Hot Wallet", "type": "CEX"},
    "0x47719227919697a59af255d81465e53b49938660": {"name": "Coinbase", "type": "CEX"},
    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": {"name": "Kraken", "type": "CEX"},
    "0xb8c77482e45f1f44de1745f52c74426c631bdd52": {"name": "BNB", "type": "CEX"},
    
    # Decentralized Exchanges (DEX) Routers / Core Contracts
    "0xef1c6e67703c7bd7107eed8303fbe6ec2554bf6b": {"name": "Uniswap V3: Router 2", "type": "DEX"},
    "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45": {"name": "Uniswap V3: Router", "type": "DEX"},
    "0xe592427a0d111dcc1498a859b4a74a5802220268": {"name": "Uniswap V3: Router 1", "type": "DEX"},
    "0x7a250d5630b4cf539739df2c5dacb4c659f2488d": {"name": "Uniswap V2: Router 2", "type": "DEX"},
    "0x1111111254fb6c44bac0bed2854e76f90643097d": {"name": "1inch: Aggregator V5", "type": "DEX"},
    "0x0000000000007f150bd6f54c40a34d7c3d5e9f56": {"name": "CowSwap: GPv2Settlement", "type": "DEX"},
    "0xd9e1c13f555eed43083c68a65b4543d37a858102": {"name": "SushiSwap: Router", "type": "DEX"},
}

def identify_address_type(address):
    """
    Checks if an address matches a known CEX or DEX signature.
    """
    if not address:
        return "Unknown", "Wallet/Contract"
        
    addr_lower = address.lower()
    if addr_lower in KNOWN_ENTITIES:
        return KNOWN_ENTITIES[addr_lower]["type"], KNOWN_ENTITIES[addr_lower]["name"]
    
    return "Unknown", "Wallet/Contract"

def save_transaction_to_csv(tx_data, file_path):
    """
    Appends or creates a CSV file containing the trace logs.
    """
    df_new = pd.DataFrame([tx_data])
    
    # Check if file exists to append or write fresh with headers
    if not os.path.isfile(file_path):
        df_new.to_csv(file_path, index=False)
    else:
        df_new.to_csv(file_path, mode='a', header=False, index=False)

def trace_wallet(wallet_address, output_file, depth=1, max_depth=3):
    """
    Recursively traces outbound ETH transfers, categorizes destinations, and saves outputs.
    """
    if depth > max_depth:
        return

    print(f"\n" + "  " * (depth - 1) + f"└── [Layer {depth}] Scanning Outbound from: {wallet_address}")
    
    params = {
        "chainid": "1",
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
        response = requests.get(BASE_URL, params=params, impersonate="chrome")
        
        if response.status_code != 200:
            print("  " * depth + f"⚠️ Server rejected connection. Status Code: {response.status_code}")
            return
            
        data = response.json()
        
        if data.get("status") == "1" and data.get("message") == "OK":
            tx_list = data["result"]
            found_outbound = False
            
            for tx in tx_list:
                if tx["from"].lower() == wallet_address.lower() and float(tx["value"]) > 0:
                    found_outbound = True
                    ether_value = float(tx["value"]) / 10**18
                    next_wallet = tx["to"]
                    tx_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(int(tx["timeStamp"])))
                    
                    # Differentiate destination exchange types
                    entity_type, entity_name = identify_address_type(next_wallet)
                    
                    # Log to console with classification indicators
                    type_flag = f"[{entity_type} - {entity_name}]" if entity_type != "Unknown" else "[Wallet/Contract]"
                    print("  " * depth + f"➡️ Sent {ether_value:.4f} ETH to {next_wallet} {type_flag} ({tx_time})")
                    print("  " * depth + f"   Tx Hash: {tx['hash']}")
                    
                    # Package structured data
                    tx_record = {
                        "layer": depth,
                        "timestamp": tx_time,
                        "tx_hash": tx['hash'],
                        "from_address": wallet_address,
                        "to_address": next_wallet,
                        "eth_value": ether_value,
                        "destination_type": entity_type,
                        "destination_name": entity_name
                    }
                    
                    # Save immediately to prevent data loss on rate limits or timeout breaks
                    save_transaction_to_csv(tx_record, output_file)
                    
                    time.sleep(1.0) 
                    
                    # Skip deeper recursive tracing if funds hit a CEX deposit router 
                    # (since CEXs pool funds, you cannot trace ownership further via simple public tx trees)
                    if entity_type == "CEX":
                        print("  " * depth + f"🛑 Flow hit a CEX ({entity_name}). Stopping branch exploration.")
                        continue
                        
                    trace_wallet(next_wallet, output_file, depth + 1, max_depth)
            
            if not found_outbound:
                print("  " * depth + "🛑 No outgoing value transfers found from this address.")
                
        else:
            print("  " * depth + f"⚠️ Etherscan Message: {data.get('result', 'No result payload')}")
            
    except Exception as e:
        print("  " * depth + f"❌ Execution error: {e}")

# Target pooling wallet discovered via MetaSleuth
pooling_wallet = "0x220fe14412bca438b3dbc5078e04f802f8f098e7"

# Generate unique run filename
timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
output_csv_filename = f"crypto_trace_{timestamp_str}.csv"

print(f"Starting secure trace on pooling wallet. Saving progress to {output_csv_filename}...")
trace_wallet(pooling_wallet, output_file=output_csv_filename, depth=1, max_depth=200)
