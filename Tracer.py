import requests
from datetime import datetime
import time

# Configuration
ETHERSCAN_API_KEY = "ZFEQKMEBZ6T7NERFNZHEFM8NIE46HRHZ9A"
USDC_CONTRACT = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"

# Integrated seed transaction hash
START_TX_HASH = "0x8274d085c74164f1f2a8e67b0ffeccd95a3c74e51c43d289de1a535d9bdb9ae0"
MAX_HOPS = 3 

# Free-tier local registry of prominent CEX deposit/hot wallets
CEX_REGISTRY = {
    "0x28c6c06298d514db089934071355e5743bf21d60": "Binance: Hot Wallet",
    "0xdfd5293d8e347dfe59e90efd55b2956a1343963d": "Binance: Deposit",
    "0xddfabcdc4d8ffc6d5beaf154f18b778f892a0740": "Paxful: Hot Wallet",
    "0x477b8d5ef7c2c42b82d4e989343a60a77f3a6192": "Kraken: Hot Wallet",
    "0x5038289369932c4a85641747ef02213e9a785d03": "Coinbase: Hot Wallet",
    "0x71660c4005ba85c37ccec51a014902af3f6e1f0e": "OKX: Deposit Wallet",
    "0xa7efae728d2936e78bda97dc267687568dd593f3": "Crypto.com: Hot Wallet",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

def get_tx_details_from_hash(tx_hash):
    """Resolves the initial transaction hash to extract sender, receiver, and timestamp metadata."""
    base_url = "https://etherscan.io"
    params = {
        "chainid": "1",
        "module": "proxy",
        "action": "eth_getTransactionByHash",
        "txhash": tx_hash,
        "apikey": ETHERSCAN_API_KEY
    }
    
    try:
        response = requests.get(base_url, params=params, headers=HEADERS)
        data = response.json()
        tx_data = data.get('result')
        
        if not tx_data:
            print(f"❌ Could not find transaction data for hash: {tx_hash}")
            return None
            
        block_params = {
            "chainid": "1",
            "module": "proxy",
            "action": "eth_getBlockByNumber",
            "tag": tx_data['blockNumber'],
            "boolean": "false",
            "apikey": ETHERSCAN_API_KEY
        }
        time.sleep(0.25)
        block_response = requests.get(base_url, params=block_params, headers=HEADERS)
        block_data = block_response.json().get('result', {})
        
        timestamp = int(block_data.get('timestamp', '0x0'), 16)
        
        input_data = tx_data.get('input', '')
        to_address = tx_data.get('to', '').lower()
        
        if to_address == USDC_CONTRACT.lower() and len(input_data) >= 138:
            decoded_to = "0x" + input_data[34:74].lower()
            raw_val = int(input_data[74:138], 16)
            value = raw_val / 10**6
        else:
            decoded_to = tx_data.get('to', '').lower()
            value = int(tx_data.get('value', '0x0'), 16) / 10**18
            
        return {
            "from": tx_data.get('from', '').lower(),
            "to": decoded_to,
            "value": value,
            "timestamp": timestamp,
            "date": datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        print(f"Error parsing origin transaction hash: {e}")
        return None

def get_outbound_hops(wallet_address, start_timestamp, end_timestamp):
    """Fetches outbound-only USDC transfers occurring strictly after the transaction's block timestamp."""
    base_url = "https://etherscan.io"
    params = {
        "chainid": "1",
        "module": "account",
        "action": "tokentx",
        "contractaddress": USDC_CONTRACT,
        "address": wallet_address,
        "sort": "asc",
        "apikey": ETHERSCAN_API_KEY
    }
    
    try:
        response = requests.get(base_url, params=params, headers=HEADERS)
        data = response.json()
    except Exception as e:
        print(f"Network error tracing {wallet_address}: {e}")
        return []

    outbound_transfers = []
    
    if data.get('status') == '0':
        if "No transactions found" in str(data.get('result')):
            return []
        print(f"❌ Etherscan V2 Error: {data.get('message')} - {data.get('result')}")
        return []
    
    if data.get('status') == '1' and isinstance(data.get('result'), list):
        for tx in data['result']:
            tx_timestamp = int(tx['timeStamp'])
            tx_from = tx['from'].lower()
            
            if start_timestamp <= tx_timestamp <= end_timestamp and tx_from == wallet_address.lower():
                outbound_transfers.append({
                    "from": tx_from,
                    "to": tx['to'].lower(),
                    "value": int(tx['value']) / 10**6,
                    "hash": tx['hash'],
                    "timestamp": tx_timestamp,
                    "date": datetime.fromtimestamp(tx_timestamp).strftime('%Y-%m-%d %H:%M:%S')
                })
                
    return outbound_transfers

def trace_outbound_tree(current_wallet, start_timestamp, end_timestamp, current_depth, max_depth, visited=None):
    """Recursively traces outbound transfers forward in time from a confirmed node location."""
    if visited is None:
        visited = set()
        
    if current_depth >= max_depth or current_wallet in visited:
        return
        
    visited.add(current_wallet)
    print(f"\n[Hop {current_depth}] Scanning forward outbound transfers for: {current_wallet}")
    
    if current_wallet in CEX_REGISTRY:
        print(f"🛑 TARGET TERMINATED: Address matches known endpoint -> {CEX_REGISTRY[current_wallet]}")
        return

    time.sleep(0.35) 
    hops = get_outbound_hops(current_wallet, start_timestamp, end_timestamp)
    
    if not hops:
        print("   ↳ (No subsequent outbound USDC movements found after this timestamp point)")
    
    for hop in hops:
        destination = hop['to']
        cex_tag = f"⚠️ [CEX DETECTED: {CEX_REGISTRY[destination]}]" if destination in CEX_REGISTRY else "[Private Wallet]"
        
        print(f"   ↳ NEXT HOP DETECTED: {hop['date']} | Out to: {destination} {cex_tag} | Amount: {hop['value']} USDC")
        
        trace_outbound_tree(destination, hop['timestamp'], end_timestamp, current_depth + 1, max_depth, visited)

def main():
    target_end_timestamp = int(time.time())
    current_time_str = datetime.fromtimestamp(target_end_timestamp).strftime('%Y-%m-%d %H:%M:%S')

    print(f"Resolving Origin Seed Transaction Hash Details: {START_TX_HASH}...")
    origin_tx = get_tx_details_from_hash(START_TX_HASH)
    
    if not origin_tx:
        print("Aborting trace setup. Unable to collect transaction origin data.")
        return
        
    print(f"\n--- SEED TRANSACTION VERIFIED ---")
    print(f"Tx Date/Time : {origin_tx['date']}")
    print(f"Sender       : {origin_tx['from']}")
    print(f"Receiver     : {origin_tx['to']}")
    print(f"Value        : {origin_tx['value']} Asset Units")
    print(f"---------------------------------")
    print(f"Tracing active from block epoch forward until: {current_time_str}\n")
    
    trace_outbound_tree(
        current_wallet=origin_tx['to'], 
        start_timestamp=origin_tx['timestamp'], 
        end_timestamp=target_end_timestamp, 
        current_depth=1, 
        max_depth=MAX_HOPS
    )

if __name__ == "__main__":
    main()
