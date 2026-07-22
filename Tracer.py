import requests
from datetime import datetime
import time

# Configuration
ETHERSCAN_API_KEY = "ZFEQKMEBZ6T7NERFNZHEFM8NIE46HRHZ9A"
START_WALLET = "0x675150eeec3cffa64d92d5d6ab5ab4cd4ef70633"

# Chronological barrier gate configuration (July 7th, 2026)
CASH_APP_DEPOSIT_TIME = "2026-07-07 00:00:00"  # Format: YYYY-MM-DD HH:MM:SS
MAX_HOPS = 3 

# Expanded registry mapping to flag centralized exit ramps instantly
CEX_REGISTRY = {
    "0x28c6c06298d514db089934071355e5743bf21d60": "Binance: Hot Wallet",
    "0xdfd5293d8e347dfe59e90efd55b2956a1343963d": "Binance: Deposit",
    "0xddfabcdc4d8ffc6d5beaf154f18b778f892a0740": "Paxful: Hot Wallet",
    "0x477b8d5ef7c2c42b82d4e989343a60a77f3a6192": "Kraken: Hot Wallet",
    "0x5038289369932c4a85641747ef02213e9a785d03": "Coinbase: Hot Wallet",
    "0x71660c4005ba85c37ccec51a014902af3f6e1f0e": "OKX: Deposit Wallet",
    "0xa7efae728d2936e78bda97dc267687568dd593f3": "Crypto.com: Hot Wallet",
}

CLIENT_HEADERS = {
    "Accept": "application/json",
    "Connection": "keep-alive"
}

def date_to_unix(date_string):
    """Converts a UTC date string into a Unix timestamp."""
    dt = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
    return int(time.mktime(dt.timetuple()))

def fetch_etherscan_v2(action_endpoint, wallet_address):
    """Safely contacts Etherscan V2 infrastructure endpoints."""
    url = "https://etherscan.io"
    params = {
        "chainid": "1",
        "module": "account",
        "action": action_endpoint,
        "address": wallet_address,
        "sort": "asc",
        "apikey": ETHERSCAN_API_KEY
    }
    try:
        response = requests.get(url, params=params, headers=CLIENT_HEADERS, timeout=15)
        if "json" in response.headers.get("Content-Type", "").lower():
            return response.json().get("result", [])
    except Exception:
        pass
    return []

def get_all_outbound_movements(wallet_address, start_timestamp, end_timestamp):
    """Gathers native ETH, internal contract sub-calls, and token movements simultaneously."""
    combined_hops = []
    
    # Layer 1 Scan: Standard ETH transaction list
    tx_list = fetch_etherscan_v2("txlist", wallet_address)
    if isinstance(tx_list, list):
        for tx in tx_list:
            if int(tx.get('timeStamp', 0)) >= start_timestamp and tx.get('from', '').lower() == wallet_address.lower():
                val = int(tx.get('value', 0)) / 10**18
                if val > 0.001:  # Filter out trivial gas dust
                    combined_hops.append({"to": tx['to'].lower(), "val": val, "asset": "ETH", "ts": int(tx['timeStamp']), "hash": tx['hash']})

    time.sleep(0.25) # Throttle for free-tier key constraints
    
    # Layer 2 Scan: Internal smart contract executions (DeFi Swaps/Mixers)
    internal_list = fetch_etherscan_v2("txlistinternal", wallet_address)
    if isinstance(internal_list, list):
        for tx in internal_list:
            if int(tx.get('timeStamp', 0)) >= start_timestamp and tx.get('from', '').lower() == wallet_address.lower():
                val = int(tx.get('value', 0)) / 10**18
                if val > 0.001:
                    combined_hops.append({"to": tx['to'].lower(), "val": val, "asset": "ETH (Internal Contract)", "ts": int(tx['timeStamp']), "hash": tx['hash']})

    time.sleep(0.25)

    # Layer 3 Scan: ERC-20 Tokens (USDC, USDT, DAI, etc.)
    token_list = fetch_etherscan_v2("tokentx", wallet_address)
    if isinstance(token_list, list):
        for tx in token_list:
            if int(tx.get('timeStamp', 0)) >= start_timestamp and tx.get('from', '').lower() == wallet_address.lower():
                decimals = int(tx.get('tokenDecimal', 18))
                val = int(tx.get('value', 0)) / 10**decimals
                if val > 1.0:  # Filter out small token dust
                    combined_hops.append({"to": tx['to'].lower(), "val": val, "asset": tx.get('tokenSymbol', 'Token'), "ts": int(tx['timeStamp']), "hash": tx['hash']})

    # Sort everything chronologically so we trace forwards correctly
    combined_hops.sort(key=lambda x: x['ts'])
    return combined_hops

def trace_forensic_tree(current_wallet, start_timestamp, end_timestamp, current_depth, max_depth, visited=None):
    """Recursively tracks any assets leaking out across multi-chain or multi-token footprints."""
    if visited is None:
        visited = set()
        
    if current_depth >= max_depth or current_wallet in visited:
        return
        
    visited.add(current_wallet)
    print(f"\n[Depth {current_depth}] Auditing ALL outbound assets for: {current_wallet}")
    
    if current_wallet in CEX_REGISTRY:
        print(f"🛑 TARGET TERMINATED: Stolen funds hit a known centralized cash-out gate -> {CEX_REGISTRY[current_wallet]}")
        return

    time.sleep(0.3)
    hops = get_all_outbound_movements(current_wallet, start_timestamp, end_timestamp)
    
    if not hops and current_depth == 0:
        print("   ↳ (No asset footprints found leaving this node. Funds are currently holding inside this wallet.)")
    
    for hop in hops:
        dest = hop['to']
        tag = f"⚠️ [CEX ENTRY DETECTED: {CEX_REGISTRY[dest]}]" if dest in CEX_REGISTRY else "[Next Private Wallet Node]"
        date_str = datetime.fromtimestamp(hop['ts']).strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"   ↳ FLIGHT DETECTED: {date_str} | Out to: {dest} {tag} | Moved: {hop['val']:.4f} {hop['asset']}")
        
        # Advance forensic focus forward in time based on this asset path execution window
        trace_forensic_tree(dest, hop['ts'], end_timestamp, current_depth + 1, max_depth, visited)

def main():
    funding_timestamp = date_to_unix(CASH_APP_DEPOSIT_TIME)
    target_end_timestamp = int(time.time())
    
    print(f"Initializing Anti-Scam Forensic Asset Tracker on Target Node: {START_WALLET}")
    print(f"Scanning Native ETH, Internal Contract Swaps, and ERC-20 Tokens since: {CASH_APP_DEPOSIT_TIME}\n")
    
    trace_forensic_tree(START_WALLET, funding_timestamp, target_end_timestamp, current_depth=0, max_depth=MAX_HOPS)

if __name__ == "__main__":
    main()
