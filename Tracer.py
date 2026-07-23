import requests
import time
import sys
import json
from datetime import datetime

# USER PARAMETERS
API_KEY = "ZFEQKMEBZ6T7NERFNZHEFM8NIE46HRHZ9A"
USDC_CONTRACT = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
START_BLOCK = "20315000"  # Focuses strictly from July 2026 onwards

START_WALLETS = [
    "0x675150eeec3cffa64d92d5d6ab5ab4cd4ef70633",
    "0xb591b2a6382025d8a39c2ad8dfd4a88d422e4f14"
]
CONSOLIDATION_HUB = "0x220fe14412bca438b3dbc5078e04f802f8f098e7"

# ETHERSCAN V2 SETTINGS
BASE_URL = "https://etherscan.io"
CHAIN_ID = "1"  # Ethereum Mainnet

# BROAD LABEL DATABASE
KNOWN_ENTITIES = {
    "0x28c6c06298d514db089934071355e5743bf21d60": ("CEX Wallet", "Binance: Hot Wallet"),
    "0xdfd5293d8e347dfe59e90efd55b2956a1343963d": ("CEX Wallet", "Binance: Deposit Hub"),
    "0xf39d22743551484a514244a31d873415410114e2": ("CEX Wallet", "Coinbase: Deposit Hub"),
    "0x71660c4dbbd0211d6641edec3e16447810444521": ("CEX Wallet", "Kraken: Deposit"),
    "0xe592427a0aece92de3edee1f18e0157c05861564": ("DEX Protocol", "Uniswap V3: Router"),
    "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45": ("DEX Protocol", "Uniswap V3: Router 2"),
    "0x1111111254fb6c44bac0bed2854e76f90643097d": ("DEX Protocol", "1inch: Aggregator"),
}

def make_v2_request(params, max_retries=3):
    """Executes safe V2 API calls with automated rate-limiting to prevent JSON decode errors."""
    params["apikey"] = API_KEY
    params["chainid"] = CHAIN_ID
    
    for attempt in range(max_retries):
        time.sleep(1.2)  # Strict 1.2s delay to fully respect free tier 5 req/sec limit
        try:
            response = requests.get(BASE_URL, params=params, timeout=15)
            if response.status_code == 429 or response.status_code == 403:
                time.sleep(5)
                continue
            
            # Safe JSON structural analysis
            try:
                data = response.json()
                if isinstance(data, dict):
                    return data
            except ValueError:
                time.sleep(3)
                continue
        except requests.exceptions.RequestException:
            time.sleep(3)
    return {}

def inspect_address_type(address):
    """Identifies the wallet classification and company link."""
    addr_lower = address.lower()
    if addr_lower in KNOWN_ENTITIES:
        return KNOWN_ENTITIES[addr_lower]
        
    res = make_v2_request({"module": "proxy", "action": "eth_getCode", "address": address, "tag": "latest"})
    code = res.get("result", "")
    
    if code and code != "0x" and isinstance(code, str):
        source_res = make_v2_request({"module": "contract", "action": "getsourcecode", "address": address})
        source = source_res.get("result", [])
        if source and isinstance(source, list) and "ContractName" in source[0]:
            return "DEX Protocol / Contract", source[0]["ContractName"]
        return "Smart Contract", "Unverified Custom Contract (Potential Mixer/Bridge)"
        
    return "Private Wallet", "Unlabeled Address (Scammer Core Hop or Fresh CEX Deposit Account)"

def get_outflows(wallet_address):
    """Tracks all possibilities: USDC, Standard ETH, and Internal Swaps."""
    outflows = []

    # 1. USDC Outflows
    res = make_v2_request({
        "module": "account", "action": "tokentx",
        "contractaddress": USDC_CONTRACT, "address": wallet_address,
        "startblock": START_BLOCK, "endblock": "99999999", "sort": "asc"
    })
    for tx in res.get("result", []) if isinstance(res.get("result"), list) else []:
        if tx['from'].lower() == wallet_address.lower():
            outflows.append({
                "type": "USDC Token", "to": tx['to'],
                "amount": f"{int(tx['value']) / 10**6:,.2f} USDC",
                "hash": tx['hash'], "time": tx['timeStamp']
            })

    # 2. Native ETH Outflows
    res = make_v2_request({
        "module": "account", "action": "txlist",
        "address": wallet_address, "startblock": START_BLOCK, "endblock": "99999999", "sort": "asc"
    })
    for tx in res.get("result", []) if isinstance(res.get("result"), list) else []:
        if tx['from'].lower() == wallet_address.lower() and int(tx.get('value', 0)) > 0:
            outflows.append({
                "type": "Standard ETH", "to": tx['to'],
                "amount": f"{int(tx['value']) / 10**18:.4f} ETH",
                "hash": tx['hash'], "time": tx['timeStamp']
            })

    # 3. Internal Contract Swaps
    res = make_v2_request({
        "module": "account", "action": "txlistinternal",
        "address": wallet_address, "startblock": START_BLOCK, "endblock": "99999999", "sort": "asc"
    })
    for tx in res.get("result", []) if isinstance(res.get("result"), list) else []:
        if tx['from'].lower() == wallet_address.lower() and int(tx.get('value', 0)) > 0:
            outflows.append({
                "type": "INTERNAL DEX Swap", "to": tx['to'],
                "amount": f"{int(tx['value']) / 10**18:.4f} ETH equiv",
                "hash": tx['hash'], "time": tx['timeStamp']
            })

    outflows.sort(key=lambda x: int(x['time']))
    return outflows

def run_forensic_audit():
    """Builds the complete text file trail map report."""
    log_filename = "forensic_trail_log.txt"
    
    with open(log_filename, "w", encoding="utf-8") as f:
        f.write("="*80 + "\n")
        f.write(f"OFFICIAL CRYPTOCURRENCY FORENSIC TRAIL MAP\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*80 + "\n\n")
        
        # Step 1: Trace Initial Funnel Wallets
        f.write("[STAGE 1: INITIAL OUTFLOW ANALYSIS]\n")
        for wallet in START_WALLETS:
            f.write(f"\nOrigin Funnel Wallet: {wallet}\n")
            outflows = get_outflows(wallet)
            if not outflows:
                f.write(" -> No outbound transactions detected in this block range.\n")
            for tx in outflows:
                w_type, company = inspect_address_type(tx['to'])
                f.write(f"  ➔ [{tx['type']}] Sent {tx['amount']} to {tx['to']}\n")
                f.write(f"    Classification: {w_type} | Company Linked: {company}\n")
                f.write(f"    Tx Hash: {tx['hash']}\n")
        
        # Step 2: Analyze Convergence Hub
        f.write("\n\n" + "="*80 + "\n")
        f.write("[STAGE 2: CONSOLIDATION HUB ANALYSIS]\n")
        f.write(f"Target Wallet Hub Address: {CONSOLIDATION_HUB}\n")
        
        hub_type, hub_company = inspect_address_type(CONSOLIDATION_HUB)
        f.write(f"Hub Classification: {hub_type} | Company Linked: {hub_company}\n")
        
        hub_outflows = get_outflows(CONSOLIDATION_HUB)
        if not hub_outflows:
            f.write("\n📍 CURRENT END POINT STATUS: FUNDS ARE CURRENTLY STAGNANT\n")
            f.write(f" -> The assets are sitting inside {CONSOLIDATION_HUB}.\n")
        else:
            f.write(f"\nOutbound movements from Consolidation Hub:\n")
            for tx in hub_outflows:
                w_type, company = inspect_address_type(tx['to'])
                f.write(f"  ➔ [{tx['type']}] Dispatched {tx['amount']} to {tx['to']}\n")
                f.write(f"    Destination Type: {w_type} | Company Linked: {company}\n")
                f.write(f"    Tx Hash: {tx['hash']}\n")
                
    print(f"✅ Success! Comprehensive trail report generated and saved to: '{log_filename}'")

def run_live_monitor():
    """Launches the clean, single-row console loop tracker for the final endpoint."""
    print("\n" + "="*80)
    print(f"LAUNCHING LIVE SENTRY MONITOR FOR CURRENT ENDPOINT")
    print("="*80)
    
    # Resolve initial profile parameters once to avoid repeating layout noise
    wallet_type, company_name = inspect_address_type(CONSOLIDATION_HUB)
    
    print(f"● WALLET TARGET : {CONSOLIDATION_HUB}")
    print(f"● TYPE CLASS    : {wallet_type}")
    print(f"● COMPANY LINK  : {company_name}")
    print("="*80)
    print("[*] Instantiating background engine. Watching for new outflows every 15s...")
    print("    [Keep this terminal open. Press Ctrl+C to stop monitor securely]\n")
    
    # Establish historic transaction benchmark
    baseline_txs = set()
    initial_flows = get_outflows(CONSOLIDATION_HUB)
    for tx in initial_flows:
        baseline_txs.add(tx['hash'])
        
    while True:
        try:
            # Check balance
            res = make_v2_request({
                "module": "account", "action": "tokenbalance",
                "contractaddress": USDC_CONTRACT, "address": CONSOLIDATION_HUB, "tag": "latest"
            })
            raw_val = res.get("result", "0")
            current_usdc = float(raw_val) / 10**6 if raw_val and not isinstance(raw_val, list) else 0.0
            
            # Check loop transaction updates
            loop_flows = get_outflows(CONSOLIDATION_HUB)
            current_hashes = {tx['hash'] for tx in loop_flows}
            
            if len(current_hashes) > len(baseline_txs):
                new_txs = current_hashes - baseline_txs
                print("\n" + "🚨" * 20)
                print("⚠️  CRITICAL ALERT: ASSETS ARE MOVING OUT OF THE HUB RIGHT NOW!")
                print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"New Outbound Tx Signatures Found: {list(new_txs)}")
                print("🚨" * 20 + "\n")
                
                sys.stdout.write('\a') # Terminal bell alert audio ping
                sys.stdout.flush()
                baseline_txs = current_hashes
            else:
                sys.stdout.write(f"\r[{datetime.now().strftime('%H:%M:%S')}] Live Tracking Status: Active | Pool Balance: {current_usdc:,.2f} USDC")
                sys.stdout.flush()
                
            time.sleep(15)
        except KeyboardInterrupt:
            print("\n\n[-] Sentry tracking stopped safely. Exiting framework.")
            break
except Exception:time.sleep(5)
if name == "main":
    run_forensic_audit()
    run_live_monitor()
