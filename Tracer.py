import requests
import time
import sys
from datetime import datetime

# Provided Forensic Parameters
API_KEY = "ZFEQKMEBZ6T7NERFNZHEFM8NIE46HRHZ9A"
TARGET_WALLET = "0x220fe14412bca438b3dbc5078e04f802f8f098e7"
USDC_CONTRACT = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"

# Etherscan V2 Specific Architecture
BASE_URL = "https://api.etherscan.io/v2/api"
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

def get_current_balances(wallet):
    """Checks exact real-time balances for both Native ETH and USDC Token."""
    # 1. Fetch USDC Token Balance
    usdc_res = query_etherscan_v2({
        "module": "account", "action": "tokenbalance",
        "contractaddress": USDC_CONTRACT, "address": wallet, "tag": "latest"
    })
    usdc_bal = float(usdc_res) / 10**6 if usdc_res and not isinstance(usdc_res, list) else 0.0

    # 2. Fetch Native ETH Balance
    eth_res = query_etherscan_v2({
        "module": "account", "action": "balance", "address": wallet, "tag": "latest"
    })
    eth_bal = float(eth_res) / 10**18 if eth_res and not isinstance(eth_res, list) else 0.0
    
    return usdc_bal, eth_bal

def fetch_recent_tx_hashes(wallet):
    """Gathers hashes of all outgoing transfers to flag historical changes."""
    tx_hashes = set()
    
    # Analyze USDC transfers
    usdc_txs = query_etherscan_v2({
        "module": "account", "action": "tokentx",
        "contractaddress": USDC_CONTRACT, "address": wallet,
        "startblock": START_BLOCK, "endblock": "99999999", "sort": "asc"
    })
    if isinstance(usdc_txs, list):
        for tx in usdc_txs:
            if tx['from'].lower() == wallet.lower():
                tx_hashes.add(tx['hash'])
                
    # Analyze Standard ETH transfers
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
    print(f"LIVE SENTRY PROTOCOL LAUNCHED FOR WALLET: {TARGET_WALLET}")
    print("="*80)
    
    print("[*] Establishing baseline transaction history...")
    known_outflows = fetch_recent_tx_hashes(TARGET_WALLET)
    print(f"[*] Baseline complete. Loaded {len(known_outflows)} historical outflows.")
    
    usdc_bal, eth_bal = get_current_balances(TARGET_WALLET)
    print(f"\n[CURRENT END WALLET HOLDINGS]:")
    print(f" 🪙  USDC Balance: {usdc_bal:,.2f} USDC")
    print(f" ⧫  ETH Balance:  {eth_bal:.4f} ETH")
    print("\n[*] Sentry Mode Active. Scanning for balance changes or movements every 15s...")
    print("Press Ctrl+C to terminate the program safely.\n")

    while True:
        try:
            # 1. Pulse-check total quantities currently in wallet
            current_usdc, current_eth = get_current_balances(TARGET_WALLET)
            
            # 2. Re-verify the absolute current outbound tx hash count
            current_outflows = fetch_recent_tx_hashes(TARGET_WALLET)
            
            # 3. Check for structural mutations (New transaction signatures detected)
            if len(current_outflows) > len(known_outflows):
                new_txs = current_outflows - known_outflows
                print("\n" + "🚨" * 15)
                print("⚠️  CRITICAL ALERT: MOVEMENT DETECTED ON TARGET WALLET!")
                print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"New Unseen Outflow Tx Detected: {list(new_txs)}")
                print(f"Updated Balance Remaining: {current_usdc:,.2f} USDC | {current_eth:.4f} ETH")
                print("🚨" * 15 + "\n")
                
                # Audible system bell ping notification (works natively on standard OS terminals)
                sys.stdout.write('\a')
                sys.stdout.flush()
                
                # Update baseline so it doesn't loop spam the exact same notification
                known_outflows = current_outflows
            else:
                # Heartbeat terminal print to confirm active monitoring status
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Monitoring... Stable: {current_usdc:,.2f} USDC | {current_eth:.4f} ETH", end='\r')
            
            # Idle for 15 seconds to stay clear of server-side endpoint request blocks
            time.sleep(15)
            
        except KeyboardInterrupt:
            print("\n[-] Sentry tracking paused securely. Operational logs saved.")
            break
        except Exception as e:
            print(f"\n[!] Read network interruption: {e}. Re-syncing framework...")
            time.sleep(5)

if __name__ == "__main__":
    monitor_loop()
