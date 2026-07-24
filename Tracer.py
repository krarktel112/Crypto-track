import time
import json
import os
import pandas as pd
from datetime import datetime
from curl_cffi import requests

# Configuration
API_KEY = "ZFEQKMEBZ6T7NERFNZHEFM8NIE46HRHZ9A"
BASE_URL = "https://api.etherscan.io/v2/api"

# Expanded list of prominent CEX Hot Wallets and Deposit Contracts
KNOWN_ENTITIES = {
    # Binance
    "0x28c6c06298d514db089934071355e5ba621b4d23": {"name": "Binance 14", "type": "CEX"},
    "0xdfd5293d8e347dfe59e90efd55b2956a1343963d": {"name": "Binance Hot Wallet", "type": "CEX"},
    "0x56eddb7aa87536c09ccc2793473599fd21a8b17f": {"name": "Binance 3", "type": "CEX"},
    "0xf977814e90da44bfa03b6295a0616a897441acec": {"name": "Binance 8", "type": "CEX"},
    
    # Coinbase
    "0x47719227919697a59af255d81465e53b49938660": {"name": "Coinbase 1", "type": "CEX"},
    "0x5038289769165b77a8ce8e30dfb1182755847eb5": {"name": "Coinbase 2", "type": "CEX"},
    "0xddfabcdc4d8ffc6d5beaf154f18b778f892a0740": {"name": "Coinbase 3", "type": "CEX"},
    
    # Kraken
    "0x267be1c1d684f78cb4f6a176c4911b741e4ffdc0": {"name": "Kraken 1", "type": "CEX"},
    "0x0a267cf51ef03a5293b33e22e30ce6f664242643": {"name": "Kraken 2", "type": "CEX"},
    
    # OKX
    "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b": {"name": "OKX 1", "type": "CEX"},
    "0xa7efae728d2936e78bda97dc267687568dd593f3": {"name": "OKX 2", "type": "CEX"},

    # Bybit
    "0xee5b5b9238e153b4e813f462a64c2ff327464201": {"name": "Bybit 1", "type": "CEX"},
    
    # Gate.io
    "0x0d0707963952f2fba59dd06f2b425ace40b492fe": {"name": "Gate.io 1", "type": "CEX"},
    
    # Core DEX Routers for reference
    "0xef1c6e67703c7bd7107eed8303fbe6ec2554bf6b": {"name": "Uniswap V3: Router 2", "type": "DEX"},
    "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45": {"name": "Uniswap V3: Router", "type": "DEX"},
    "0x7a250d5630b4cf539739df2c5dacb4c659f2488d": {"name": "Uniswap V2: Router 2", "type": "DEX"},
    "0x1111111254fb6c44bac0bed2854e76f90643097d": {"name": "1inch: Aggregator V5", "type": "DEX"},
}

def identify_address_type(address):
    if not address:
        return "Unknown", "Wallet/Contract"
    addr_lower = address.lower()
    if addr_lower in KNOWN_ENTITIES:
        return KNOWN_ENTITIES[addr_lower]["type"], KNOWN_ENTITIES[addr_lower]["name"]
    return "Unknown", "Wallet/Contract"

def save_transaction_to_csv(tx_data, file_path):
    df_new = pd.DataFrame([tx_data])
    if not os.path.isfile(file_path):
        df_new.to_csv(file_path, index=False)
    else:
        df_new.to_csv(file_path, mode='a', header=False, index=False)

def trace_wallet(wallet_address, output_file, depth=1, max_depth=3):
    if depth > max_depth:
        return

    print(f"\n" + "  " * (depth - 1) + f"└── [Layer {depth}] Scanning Outbound from: {wallet_address}")
    
    page = 1
    offset = 100  # Pull 100 transactions at a time to be comprehensive
    has_more_tx = True
    found_outbound = False
    
    while has_more_tx:
        params = {
            "chainid": "1",
            "module": "account",
            "action": "txlist",
            "address": wallet_address,
            "startblock": 0,
            "endblock": 99999999, # Covers all blocks up to today
            "page": page,
            "offset": offset, 
            "sort": "desc", # Newest first
            "apikey": API_KEY
        }
        
        try:
            # Respect Etherscan standard rate limits (Max 5 requests per second)
            time.sleep(0.2) 
            response = requests.get(BASE_URL, params=params, impersonate="chrome")
            
            if response.status_code != 200:
                print("  " * depth + f"⚠️ Server rejected connection. Status Code: {response.status_code}")
                break
                
            data = response.json()
            
            if data.get("status") == "1" and data.get("message") == "OK":
                tx_list = data["result"]
                
                # If we get fewer transactions than the offset, it's the last page
                if len(tx_list) < offset:
                    has_more_tx = False
                
                for tx in tx_list:
                    if tx["from"].lower() == wallet_address.lower() and float(tx["value"]) > 0:
                        found_outbound = True
                        ether_value = float(tx["value"]) / 10**18
                        next_wallet = tx["to"]
                        tx_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(int(tx["timeStamp"])))
                        
                        entity_type, entity_name = identify_address_type(next_wallet)
                        type_flag = f"[{entity_type} - {entity_name}]" if entity_type != "Unknown" else "[Wallet/Contract]"
                        
                        print("  " * depth + f"➡️ Sent {ether_value:.4f} ETH to {next_wallet} {type_flag} ({tx_time})")
                        print("  " * depth + f"   Tx Hash: {tx['hash']}")
                        
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
                        
                        save_transaction_to_csv(tx_record, output_file)
                        
                        if entity_type == "CEX":
                            print("  " * depth + f"🛑 Flow hit a CEX ({entity_name}). Stopping branch exploration.")
                            continue
                            
                        # Recursive step for downstream trace
                        trace_wallet(next_wallet, output_file, depth + 1, max_depth)
                
                page += 1 # Advance to next page of transactions for this wallet
                
            else:
                # No transactions found or end of lists
                has_more_tx = False
                if not found_outbound and page == 1:
                    print("  " * depth + "🛑 No outgoing value transfers found from this address.")
                
        except Exception as e:
            print("  " * depth + f"❌ Execution error: {e}")
            has_more_tx = False

# Target pooling wallet discovered via MetaSleuth
pooling_wallet = "0x220fe14412bca438b3dbc5078e04f802f8f098e7"

# Generate unique run filename
timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
output_csv_filename = f"crypto_trace_{timestamp_str}.csv"

print(f"Starting secure complete trace on pooling wallet. Saving progress to {output_csv_filename}...")
# Kept max_depth at 5 to prevent endless scraping loops on massive charts
trace_wallet(pooling_wallet, output_file=output_csv_filename, depth=1, max_depth=5)
