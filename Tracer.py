import requests
from datetime import datetime
import time

# Configuration
ETHERSCAN_API_KEY = "ZFEQKMEBZ6T7NERFNZHEFM8NIE46HRHZ9A"
USDC_CONTRACT = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"

# Updated recipient address that received the funds from Cash App
START_WALLET = "0x675150eeec3cffa64d92d5d6ab5ab4cd4ef70633"

# Set this to the approximate date and time Cash App sent the deposit
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
    """Fetches outbound-only USDC transfers after the Cash App funding time using Etherscan API V2."""
    base_url = "https://etherscan.io"
    
    params = {
        "chainid": "1",  # Ethereum Mainnet
        "module": "account",
        "action": "tokentx",
        "contractaddress": USDC_CONTRACT,
        "address": wallet_address,
        "sort": "asc",
        "apikey": ETHERSCAN_API_KEY
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(base_url, params=params, headers=headers)
        
        if "Content-Type" in response.headers and "json" not in response.headers["Content-Type"].lower():
            print(f"⚠️ API format unexpected. Status code: {response.status_code}")
            return []
            
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
            
            # Enforce gate: Must be after Cash App deposit time and strictly outbound
            if start_timestamp <= tx_timestamp <= end_timestamp and tx_from == wallet_address.lower():
                outbound_transfers.append({
                    "from": tx_from,
                    "to": tx['to'].lower(),
                    "value": int(tx['value']) / 10**6,  # 6 decimal places for USDC
                    "hash": tx['hash'],
                    "timestamp": tx_timestamp,
                    "date": datetime.fromtimestamp(tx_timestamp).strftime('%Y-%m-%d %H:%M:%S')
                })
                
    return outbound_transfers

def trace_outbound_tree(current_wallet, start_timestamp, end_timestamp, current_depth, max_depth, visited=None):
    """Recursively traces cascading outbound transfers forward in time from the funding event."""
    if visited is None:
        visited = set()
        
    if current_depth >= max_depth or current_wallet in visited:
        return
        
    visited.add(current_wallet)
    print(f"\n[Depth {current_depth}] Tracing outbound movements for wallet: {current_wallet}")
    
    if current_wallet in CEX_REGISTRY:
        print(f"🛑 TARGET TERMINATED: Funds reached a known exchange -> {CEX_REGISTRY[current_wallet]}")
        return

    time.sleep(0.35)  # Safety delay for free key tiers
    
    hops = get_outbound_hops(current_wallet, start_timestamp, end_timestamp)
    
    if not hops and current_depth == 0:
        print(f"   ↳ (No outbound USDC movements found after the Cash App funding timestamp)")
    
    for hop in hops:
        destination = hop['to']
        cex_tag = f"⚠️ [CEX DETECTED: {CEX_REGISTRY[destination]}]" if destination in CEX_REGISTRY else "[Private Wallet]"
        
        print(f"   ↳ HOP DETECTED: {hop['date']} | Out to: {destination} {cex_tag} | Amount: {hop['value']} USDC")
        
        # Keep cascading the timeline window forward 
        trace_outbound_tree(destination, hop['timestamp'], end_timestamp, current_depth + 1, max_depth, visited)

def main():
    funding_timestamp = date_to_unix(CASH_APP_DEPOSIT_TIME)
    target_end_timestamp = int(time.time())
    current_date_str = datetime.fromtimestamp(target_end_timestamp).strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"Starting Outbound Tracker on Cash App Funded Destination: {START_WALLET}")
    print(f"Analyzing all movements from funding time ({CASH_APP_DEPOSIT_TIME}) up to today ({current_date_str})\n")
    
    trace_outbound_tree(START_WALLET, funding_timestamp, target_end_timestamp, current_depth=0, max_depth=MAX_HOPS)

if __name__ == "__main__":
    main()
