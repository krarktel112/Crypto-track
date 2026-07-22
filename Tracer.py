import requests
from datetime import datetime
import time

# Configuration
ETHERSCAN_API_KEY = "ZFEQKMEBZ6T7NERFNZHEFM8NIE46HRHZ9A"
START_WALLET = "0x675150eeec3cffa64d92d5d6ab5ab4cd4ef70633"
CASH_APP_DEPOSIT_TIME = "2026-07-07 00:00:00"  # Format: YYYY-MM-DD HH:MM:SS
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

def date_to_unix(date_string):
    """Converts a UTC date string into a Unix timestamp."""
    dt = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
    return int(time.mktime(dt.timetuple()))

def get_outbound_hops(wallet_address, start_timestamp, end_timestamp):
    """Fetches outbound native ETH movements with deep terminal diagnostic printouts."""
    base_url = "https://etherscan.io"
    
    params = {
        "chainid": "1",          # Ethereum Mainnet
        "module": "account",
        "action": "txlist",      # Targets base ETH movements
        "address": wallet_address,
        "sort": "asc",
        "apikey": ETHERSCAN_API_KEY
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(base_url, params=params, headers=headers)
        data = response.json()
    except Exception as e:
        print(f"Network error tracing {wallet_address}: {e}")
        return []

    # Diagnostics block: Print raw internal Etherscan payload status codes directly to the terminal
    if data.get('status') == '0':
        message = data.get('message', '')
        result = data.get('result', '')
        
        # Suppress noise if the wallet simply has zero historical logs
        if "No transactions found" in str(result):
            return []
            
        print(f"❌ Internal Etherscan API Rejection Message: [{message}] - Details: {result}")
        return []

    outbound_transfers = []
    
    if data.get('status') == '1' and isinstance(data.get('result'), list):
        for tx in data['result']:
            tx_timestamp = int(tx['timeStamp'])
            tx_from = tx['from'].lower()
            
            if start_timestamp <= tx_timestamp <= end_timestamp and tx_from == wallet_address.lower():
                tx_value = int(tx['value']) / 10**18  # Native ETH decimals conversion
                
                if tx_value > 0:
                    outbound_transfers.append({
                        "from": tx_from,
                        "to": tx['to'].lower(),
                        "value": tx_value,
                        "hash": tx['hash'],
                        "timestamp": tx_timestamp,
                        "date": datetime.fromtimestamp(tx_timestamp).strftime('%Y-%m-%d %H:%M:%S')
                    })
                
    return outbound_transfers

def trace_outbound_tree(current_wallet, start_timestamp, end_timestamp, current_depth, max_depth, visited=None):
    """Recursively traces cascading outbound native money transfers and flags exchange matches."""
    if visited is None:
        visited = set()
        
    if current_depth >= max_depth or current_wallet in visited:
        return
        
    visited.add(current_wallet)
    print(f"\n[Depth {current_depth}] Scanning outbound native hops for: {current_wallet}")
    
    if current_wallet in CEX_REGISTRY:
        print(f"🛑 TARGET TERMINATED: Money reached known exchange endpoint -> {CEX_REGISTRY[current_wallet]}")
        return

    time.sleep(0.35) 
    hops = get_outbound_hops(current_wallet, start_timestamp, end_timestamp)
    
    if not hops and current_depth == 0:
        print(f"   ↳ (No outbound native money movements found between {CASH_APP_DEPOSIT_TIME} and today)")
    
    for hop in hops:
        destination = hop['to']
        cex_tag = f"⚠️ [CEX DETECTED: {CEX_REGISTRY[destination]}]" if destination in CEX_REGISTRY else "[Private Wallet]"
        
        print(f"   ↳ HOP DETECTED: {hop['date']} | Out to: {destination} {cex_tag} | Amount: {hop['value']:.5f} ETH")
        trace_outbound_tree(destination, hop['timestamp'], end_timestamp, current_depth + 1, max_depth, visited)

def main():
    funding_timestamp = date_to_unix(CASH_APP_DEPOSIT_TIME)
    target_end_timestamp = int(time.time())
    
    current_date_str = datetime.fromtimestamp(target_end_timestamp).strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"Starting CEX-Aware Native Outbound Tracker from Cash App Target: {START_WALLET}")
    print(f"Tracking interval: {CASH_APP_DEPOSIT_TIME} to {current_date_str}\n")
    
    trace_outbound_tree(START_WALLET, funding_timestamp, target_end_timestamp, current_depth=0, max_depth=MAX_HOPS)

if __name__ == "__main__":
    main()
