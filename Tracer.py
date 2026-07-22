import requests
from datetime import datetime
import time

# Configuration
ETHERSCAN_API_KEY = "ZFEQKMEBZ6T7NERFNZHEFM8NIE46HRHZ9A"
START_WALLET = "0x675150eeec3cffa64d92d5d6ab5ab4cd4ef70633"

# Chronological tracking window gate (July 7th, 2026)
CASH_APP_DEPOSIT_TIME = "2026-07-07 00:00:00"  # Format: YYYY-MM-DD HH:MM:SS
MAX_HOPS = 4  # Increased depth to track through complex swaps

# Expanded registry covering Centralized Exchanges (CEX) and high-risk mixers/bridges
DEFI_CEX_REGISTRY = {
    # Centralized Exit Ramps
    "0x28c6c06298d514db089934071355e5743bf21d60": "Binance: Hot Wallet",
    "0xdfd5293d8e347dfe59e90efd55b2956a1343963d": "Binance: Deposit",
    "0xddfabcdc4d8ffc6d5beaf154f18b778f892a0740": "Paxful: Hot Wallet",
    "0x477b8d5ef7c2c42b82d4e989343a60a77f3a6192": "Kraken: Hot Wallet",
    "0x5038289369932c4a85641747ef02213e9a785d03": "Coinbase: Hot Wallet",
    "0x71660c4005ba85c37ccec51a014902af3f6e1f0e": "OKX: Deposit Wallet",
    "0xa7efae728d2936e78bda97dc267687568dd593f3": "Crypto.com: Hot Wallet",
    
    # Decentralized Exchanges (DEX) Routers - Used for swapping coins
    "0xef1c6e67703c7bd7107eed8303fbe6ec2554bf6b": "Uniswap V3: Router",
    "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45": "Uniswap V3: Router 2",
    "0x7a250d5630b4cf539739df2c5dacb4c659f2488d": "Uniswap V2: Router",
    "0x1111111254fb6c44bac0bed2854e76f90643097d": "1inch: Aggregator Router",
    "0xd9e1ce17f2641f24ae83637ab66a2cca9c378b9f": "SushiSwap: Router",
    
    # Cross-Chain Bridges (Moving funds to Base, Arbitrum, Solana, etc.)
    "0x490480447d25e8605515edaf4442240d42125013": "Base Bridge Engine",
    "0xa3aee242c35be26e926a457497d39aa48d3db64d": "Arbitrum One Bridge Gateway",
}

CLIENT_HEADERS = {"Accept": "application/json", "Connection": "keep-alive"}

def date_to_unix(date_string):
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

def trace_internal_swap_recipient(tx_hash, target_wallet):
    """Parses transaction receipts to extract the actual recipient wallet address after a swap."""
    url = "https://etherscan.io"
    params = {
        "chainid": "1",
        "module": "proxy",
        "action": "eth_getTransactionReceipt",
        "txhash": tx_hash,
        "apikey": ETHERSCAN_API_KEY
    }
    try:
        response = requests.get(url, params=params, headers=CLIENT_HEADERS, timeout=15)
        result = response.json().get("result", {})
        logs = result.get("logs", [])
        
        # Scammers swap to stablecoins. Look for the last internal transfer log destination
        for log in reversed(logs):
            topics = log.get("topics", [])
            # ERC-20 Transfer Event Signature: 0xddf252ad...
            if len(topics) == 3 and topics[0].lower().startswith("0xddf252ad"):
                potential_recipient = "0x" + topics[2][-40:]
                if potential_recipient.lower() != target_wallet.lower() and potential_recipient.lower() not in DEFI_CEX_REGISTRY:
                    return potential_recipient.lower()
    except Exception:
        pass
    return None

def get_all_outbound_movements(wallet_address, start_timestamp, end_timestamp):
    """Gathers native ETH, internal contract sub-calls, and token movements simultaneously."""
    combined_hops = []
    
    # Layer 1 Scan: Standard ETH transaction list
    tx_list = fetch_etherscan_v2("txlist", wallet_address)
    if isinstance(tx_list, list):
        for tx in tx_list:
            if int(tx.get('timeStamp', 0)) >= start_timestamp and tx.get('from', '').lower() == wallet_address.lower():
                val = int(tx.get('value', 0)) / 10**18
                if val > 0.001:
                    combined_hops.append({"to": tx['to'].lower(), "val": val, "asset": "ETH", "ts": int(tx['timeStamp']), "hash": tx['hash']})

    time.sleep(0.2)
    
    # Layer 2 Scan: Internal smart contract executions (DeFi Swaps/Mixers)
    internal_list = fetch_etherscan_v2("txlistinternal", wallet_address)
    if isinstance(internal_list, list):
        for tx in internal_list:
            if int(tx.get('timeStamp', 0)) >= start_timestamp and tx.get('from', '').lower() == wallet_address.lower():
                val = int(tx.get('value', 0)) / 10**18
                if val > 0.001:
                    combined_hops.append({"to": tx['to'].lower(), "val": val, "asset": "ETH (Internal Contract)", "ts": int(tx['timeStamp']), "hash": tx['hash']})

    time.sleep(0.2)

    # Layer 3 Scan: ERC-20 Tokens (USDC, USDT, DAI, wrapped assets)
    token_list = fetch_etherscan_v2("tokentx", wallet_address)
    if isinstance(token_list, list):
        for tx in token_list:
            if int(tx.get('timeStamp', 0)) >= start_timestamp and tx.get('from', '').lower() == wallet_address.lower():
                decimals = int(tx.get('tokenDecimal', 18))
                val = int(tx.get('value', 0)) / 10**decimals
                if val > 1.0:
                    combined_hops.append({"to": tx['to'].lower(), "val": val, "asset": tx.get('tokenSymbol', 'Token'), "ts": int(tx['timeStamp']), "hash": tx['hash']})

    combined_hops.sort(key=lambda x: x['ts'])
    return combined_hops

def trace_forensic_tree(current_wallet, start_timestamp, end_timestamp, current_depth, max_depth, visited=None):
    """Recursively tracks assets leaking out, dynamically jumping through swap routers and bridges."""
    if visited is None:
        visited = set()
        
    if current_depth >= max_depth or current_wallet in visited:
        return
        
    visited.add(current_wallet)
    print(f"\n[Depth {current_depth}] Auditing ALL outbound pathways for: {current_wallet}")
    
    if current_wallet in DEFI_CEX_REGISTRY and "Hot Wallet" in DEFI_CEX_REGISTRY[current_wallet]:
        print(f"🛑 CRITICAL ENDPOINT: Funds hit a known exchange cash-out gate -> {DEFI_CEX_REGISTRY[current_wallet]}")
        return

    time.sleep(0.3)
    hops = get_all_outbound_movements(current_wallet, start_timestamp, end_timestamp)
    
    if not hops and current_depth == 0:
        print("   ↳ (No asset footprints found leaving this node. Funds are holding inside this wallet.)")
    
    for hop in hops:
        dest = hop['to']
        date_str = datetime.fromtimestamp(hop['ts']).strftime('%Y-%m-%d %H:%M:%S')
        
        # Scenario A: Funds hit a Centralized Exchange
        if dest in DEFI_CEX_REGISTRY and "Hot Wallet" in DEFI_CEX_REGISTRY[dest]:
            print(f"   ↳ 🚨 CEX TARGET EXPOSED: {date_str} | Out to: {dest} [{DEFI_CEX_REGISTRY[dest]}] | Amount: {hop['val']:.2f} {hop['asset']}")
            print(f"      👉 Action: Subpoena this exchange immediately using Tx Hash: {hop['hash']}")
            continue
            
        # Scenario B: Funds hit a Decentralized Exchange Router or Bridge to Swap Coins
        elif dest in DEFI_CEX_REGISTRY:
            router_name = DEFI_CEX_REGISTRY[dest]
            print(f"   ↳ 🔄 DEX/BRIDGE SWAP INTERCEPTED: {date_str} | Funds moved into [{router_name}] via Hash: {hop['hash']}")
            print("      🔍 Decoding event logs to track the post-swap output address...")
            
            time.sleep(0.3)
            real_recipient = trace_internal_swap_recipient(hop['hash'], current_wallet)
            
            if real_recipient:
                print(f"      ↳ 🎯 Trail recovered! Post-swap funds redirected out to: {real_recipient}")
                trace_forensic_tree(real_recipient, hop['ts'], end_timestamp, current_depth + 1, max_depth, visited)
            else:
                print("      ↳ (Liquidity pool exit address matched a nested compiler router or multi-sig vault; trail obscured.)")
                
        # Scenario C: Regular Wallet-to-Wallet Hop
        else:
            print(f"   ↳ FLIGHT DETECTED: {date_str} | Out to: {dest} [Private Wallet Node] | Moved: {hop['val']:.4f} {hop['asset']}")
            trace_forensic_tree(dest, hop['ts'], end_timestamp, current_depth + 1, max_depth, visited)

def main():
    funding_timestamp = date_to_unix(CASH_APP_DEPOSIT_TIME)
    target_end_timestamp = int(time.time())
    
    print("=======================================================================")
    print("      DEFI-INTELLIGENCE ADVANCED SWAP-AWARE ASSET TRACKER              ")
    print("=======================================================================")
    print(f"Scam Target Node Address : {START_WALLET}")
    print(f"Chronological Scan Start : {CASH_APP_DEPOSIT_TIME}")
    print("-----------------------------------------------------------------------\n")
    
    trace_forensic_tree(START_WALLET, funding_timestamp, target_end_timestamp, current_depth=0, max_depth=MAX_HOPS)

if __name__ == "__main__":
    main()
