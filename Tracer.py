import requests
import time
from datetime import datetime

# Configuration
API_KEY = "ZFEQKMEBZ6T7NERFNZHEFM8NIE46HRHZ9A"
CONSOLIDATION_WALLET = "0x220fe14412bca438b3dbc5078e04f802f8f098e7"
USDC_CONTRACT = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"

# Etherscan V2 Requirements
BASE_URL = "https://etherscan.io"
CHAIN_ID = "1"  # 1 specifies the Ethereum Mainnet Network
START_BLOCK = "20315000"  # Approximates July 17th, 2026 onwards

def make_safe_v2_request(params, max_retries=3):
    """Executes safe API calls against the mandated Etherscan V2 architecture."""
    params["apikey"] = API_KEY
    params["chainid"] = CHAIN_ID  # Required for all V2 endpoints
    
    for attempt in range(max_retries):
        time.sleep(1.0)  # Throttles traffic to stay under free limits
        try:
            response = requests.get(BASE_URL, params=params, timeout=10)
            
            if response.status_code != 200:
                continue
                
            try:
                data = response.json()
                if data.get("status") == "1":
                    return data.get("result", [])
                elif "switch to Etherscan API V2" in str(data.get("result")):
                    print("    🛑 Critical: API routing configuration mismatch.")
                    return []
                else:
                    return []
            except ValueError:
                continue
        except requests.exceptions.RequestException:
            time.sleep(2)
            
    return []

def get_pivot_outflows(wallet_address):
    """Gathers all outbound paths using V2 endpoints."""
    outflows = []

    print("[*] Scan 1/3: Analyzing Outbound USDC Token Transfers...")
    usdc_txs = make_safe_v2_request({
        "module": "account", "action": "tokentx",
        "contractaddress": USDC_CONTRACT, "address": wallet_address,
        "startblock": START_BLOCK, "endblock": "99999999", "sort": "asc"
    })
    for tx in usdc_txs:
        if tx['from'].lower() == wallet_address.lower():
            outflows.append({
                "type": "USDC Token", "to": tx['to'],
                "amount": f"{int(tx['value']) / 10**6:,.2f} USDC",
                "hash": tx['hash'], "time": tx['timeStamp']
            })

    print("[*] Scan 2/3: Analyzing Outbound Base Layer ETH Transfers...")
    eth_txs = make_safe_v2_request({
        "module": "account", "action": "txlist",
        "address": wallet_address, "startblock": START_BLOCK,
        "endblock": "99999999", "sort": "asc"
    })
    for tx in eth_txs:
        if tx['from'].lower() == wallet_address.lower() and int(tx['value']) > 0:
            outflows.append({
                "type": "Standard ETH", "to": tx['to'],
                "amount": f"{int(tx['value']) / 10**18:.4f} ETH",
                "hash": tx['hash'], "time": tx['timeStamp']
            })

    print("[*] Scan 3/3: Analyzing Internal Smart Contract Swaps/Executions...")
    internal_txs = make_safe_v2_request({
        "module": "account", "action": "txlistinternal",
        "address": wallet_address, "startblock": START_BLOCK,
        "endblock": "99999999", "sort": "asc"
    })
    for tx in internal_txs:
        if tx['from'].lower() == wallet_address.lower() and int(tx['value']) > 0:
            outflows.append({
                "type": "INTERNAL Contract Execution", "to": tx['to'],
                "amount": f"{int(tx['value']) / 10**18:.4f} ETH equiv",
                "hash": tx['hash'], "time": tx['timeStamp']
            })

    outflows.sort(key=lambda x: int(x['time']))
    return outflows

def check_destination_info(address):
    """Checks if target node is an automated contract or user deposit wallet."""
    code = make_safe_v2_request({"module": "proxy", "action": "eth_getCode", "address": address, "tag": "latest"})
    if code and code != "0x":
        return "Smart Contract Protocol (DEX/Bridge/Mixer)"
    return "Private Deposit/User Wallet Address"

def run_pivot_trace():
    print("="*80)
    print(f"TARGETED CONSOLIDATION TRACE (V2 API) FOR: {CONSOLIDATION_WALLET}")
    print("="*80)
    
    outflows = get_pivot_outflows(CONSOLIDATION_WALLET)
    
    if not outflows:
        print("\n📍 STATUS: Funds are officially stagnant inside this third wallet.")
        print("➡️ Meaning: The scammer has pooled the funds here but has not moved them yet.")
        return outflows

    print(f"\n✅ ALERT: Outbound Movements Detected ({len(outflows)}):")
    for tx in outflows:
        dest_type = check_destination_info(tx['to'])
        tx_time = datetime.fromtimestamp(int(tx['time'])).strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"➔ [{tx['type']}] Dispatched {tx['amount']}")
        print(f"  Destination Node: {tx['to']} ({dest_type})")
        print(f"  Timestamp:        {tx_time}")
        print(f"  Tx Hash:          {tx['hash']}\n")
        print("-" * 50)
    return outflows

if __name__ == "__main__":
    run_pivot_trace()
