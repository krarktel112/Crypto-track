import requests
import time
import sys
from datetime import datetime

# Provided Forensic Parameters
API_KEY = "ZFEQKMEBZ6T7NERFNZHEFM8NIE46HRHZ9A"
TARGET_WALLET = "0x220fe14412bca438b3dbc5078e04f802f8f098e7"
USDC_CONTRACT = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"

# Etherscan V2 Specific Architecture
BASE_URL = "https://etherscan.io"
CHAIN_ID = "1"  # Ethereum Mainnet
START_BLOCK = "20315000"  # Target timeframe benchmark

def query_etherscan_v2(params):
    """Executes rate-limited safety calls to Etherscan V2 structure."""
    params["apikey"] = API_KEY
    params["chainid"] = CHAIN_ID
    time.sleep(1.1)  # Strict baseline throttle to respect free API key limit
    try:
        response = requests.get(BASE_URL, params=params, timeout=12)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "1":
                return data.get("result", [])
    except Exception:
        pass
    return []

def resolve_wallet_identity(address):
    """Detects if address is a CEX deposit, a DEX contract, or an unknown user wallet."""
    # 1. First check if it is a Smart Contract code address
    code = query_etherscan_v2({"module": "proxy", "action": "eth_getCode", "address": address, "tag": "latest"})
    
    if code and code != "0x":
        # Pull contract metadata name to discover DEX platforms
        source = query_etherscan_v2({"module": "contract", "action": "getsourcecode", "address": address})
        if source and isinstance(source, list) and len(source) > 0 and "ContractName" in source[0]:
            name = source[0]["ContractName"]
            return f"DEX (Decentralized Exchange Smart Contract)", name
        return "Smart Contract", "Unknown Protocol / Custom Automated Script"
        
    # 2. Check if the address matches known CEX / DEX hot wallets or common tracking tags
    address_lower = address.lower()
    known_labels = {
        "0x28c6c06298d514db089934071355e5743bf21d60": ("CEX Wallet", "Binance"),
        "0xdfd5293d8e347dfe59e90efd55b2956a1343963d": ("CEX Wallet", "Binance Deposit Hub"),
        "0xf39d22743551484a514244a31d873415410114e2": ("CEX Wallet", "Coinbase Deposit Hub"),
        "0x71660c4dbbd0211d6641edec3e16447810444521": ("CEX Wallet", "Kraken"),
        "0xe592427a0aece92de3edee1f18e0157c05861564": ("DEX Protocol", "Uniswap V3 Router"),
        "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45": ("DEX Protocol", "Uniswap V3 Router 2"),
        "0x1111111254fb6c44bac0bed2854e76f90643097d": ("DEX Protocol", "1inch Router"),
    }
    
    if address_lower in known_labels:
        return known_labels[address_lower]
        
    # Default fallback: If it has no contract code, it's an unlabelled private address/deposit bucket
    return "Private Wallet", "Unlabeled Address (Likely Scammer Stash or New Exchange Account)"

def get_current_balances(wallet):
    """Checks exact real-time balances for both Native ETH and USDC Token."""
    usdc_res = query_etherscan_v2({
        "module": "account", "action": "tokenbalance",
        "contractaddress": USDC_CONTRACT, "address": wallet, "tag": "latest"
    })
    usdc_bal = float(usdc_res) / 10**6 if usdc_res and not isinstance(usdc_res, list) else 0.0

    eth_res = query_etherscan_v2({
        "module": "account", "action": "balance", "address": wallet, "tag": "latest"
    })
    eth_bal = float(eth_res) / 10**18 if eth_res and not isinstance(eth_res, list) else 0.0
    
    return usdc_bal, eth_bal

def fetch_recent_tx_hashes(wallet):
    """Gathers hashes of all outgoing transfers to flag historical changes."""
    tx_hashes = set()
    
    usdc_txs = query_etherscan_v2({
        "module": "account", "action": "tokentx",
        "contractaddress": USDC_CONTRACT, "address": wallet,
        "startblock": START_BLOCK, "endblock": "99999999", "sort": "asc"
    })
    if isinstance(usdc_txs, list):
        for tx in usdc_txs:
            if tx['from'].lower() == wallet.lower():
                tx_hashes.add(tx['hash'])
                
    eth_txs = query_etherscan_v2({
        "module": "account", "action": "txlist",
        "address": wallet, "startblock": START_BLOCK,
        "endblock": "99999999", "sort": "asc"
    })
    if isinstance(eth_txs, list):
        for tx in eth_txs:
            if tx['from'].lower() == wallet.lower() and int(tx['value']) > 0:
                tx_hashes.add(tx['hash'])
                
    return tx_hashes

def monitor_loop():
    print("="*80)
    print("      BLOCKCHAIN FORENSIC TARGET SCANNER (API V2 OVERHAUL)")
    print("="*80)
    
    # 1. Resolve Target Metadata ONCE at startup
    print("[*] Contacting node registry to identify wallet platform...")
    wallet_type, company_name = resolve_wallet_identity(TARGET_WALLET)
    usdc_bal, eth_bal = get_current_balances(TARGET_WALLET)
    known_outflows = fetch_recent_tx_hashes(TARGET_WALLET)
    
    print("\n" + "-"*80)
    print(f" TARGET WALLET ADDRESS : {TARGET_WALLET}")
    print(f" CLASSIFICATION TYPE   : {wallet_type}")
    print(f" IDENTIFIED PLATFORM   : {company_name}")
    print("-"*80)
    print(f" CURRENT HOLDINGS      : {usdc_bal:,.2f} USDC  |  {eth_bal:.4f} ETH")
    print(f" HISTORICAL OUTFLOWS   : {len(known_outflows)} recorded exit traces")
    print("-"*80 + "\n")
    
    print("[*] Sentry Settle Mode Activated. Watching live for movement every 15s...")
    print("    [Keep window running. Press Ctrl+C to terminate at any time]\n")

    while True:
        try:
            current_usdc, current_eth = get_current_balances(TARGET_WALLET)
            current_outflows = fetch_recent_tx_hashes(TARGET_WALLET)
            
            if len(current_outflows) > len(known_outflows):
                new_txs = current_outflows - known_outflows
                print("\n" + "🚨" * 15)
                print("⚠️  CRITICAL INFRASTRUCTURE ALERT: FUNDS SENT OUTWARD!")
                print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Executed Tx Signatures: {list(new_txs)}")
                print(f"Remaining Capital Left: {current_usdc:,.2f} USDC")
                print("🚨" * 15 + "\n")
                
                # Audible Terminal Bell
                sys.stdout.write('\a')
                sys.stdout.flush()
                
                known_outflows = current_outflows
            else:
                # Single-row updating terminal screen layout update
                sys.stdout.write(f"\r[{datetime.now().strftime('%H:%M:%S')}] Live Sync Status: Stable Balances ({current_usdc:,.2f} USDC)")
                sys.stdout.flush()
            
            time.sleep(15)
            
        except KeyboardInterrupt:
            print("\n\n[-] Sentry tracking paused securely. Program exited.")
            break
        except Exception as e:
            time.sleep(5)

if __name__ == "__main__":
    monitor_loop()
