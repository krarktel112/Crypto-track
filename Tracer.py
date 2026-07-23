import requests
import time
from datetime import datetime

# Configuration
API_KEY = "ZFEQKMEBZ6T7NERFNZHEFM8NIE46HRHZ9A"
CONSOLIDATION_WALLET = "0x220fe14412bca438b3dbc5078e04f802f8f098e7"
USDC_CONTRACT = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"

# Target block approximate for mid-July 2026 onwards
START_BLOCK = "20315000" 
BASE_URL = "https://api.etherscan.io/api"

def make_safe_request(params, max_retries=3):
    """Executes safe API calls with explicit rate limiting and JSON safety nets."""
    params["apikey"] = API_KEY
    
    for attempt in range(max_retries):
        time.sleep(1.0)  # Increased delay to 1 full second to completely bypass the 5 req/sec limit
        try:
            response = requests.get(BASE_URL, params=params, timeout=10)
            
            # Catch standard HTTP errors (like 403 Forbidden or 429 Too Many Requests)
            if response.status_code != 200:
                print(f"    ⚠️ HTTP Error Status: {response.status_code}. Retrying...")
                continue
                
            # Verify if content is actually JSON before decoding
            try:
                data = response.json()
                if data.get("status") == "1":
                    return data.get("result", [])
                elif data.get("message") == "NOTOK":
                    print(f"    ⚠️ Etherscan Message: {data.get('result')}")
                    return []
                else:
                    return []
            except ValueError:
                print(f"    ⚠️ Received non-JSON response from server (Attempt {attempt+1}/{max_retries}).")
                if "cloudflare" in response.text.lower():
                    print("    🛑 Cloudflare Block: Etherscan is throttling your IP address. Waiting 5 seconds...")
                    time.sleep(5)
                continue
                
        except requests.exceptions.RequestException as e:
            print(f"    ⚠️ Connection error: {e}. Retrying...")
            time.sleep(2)
            
    return []

def get_pivot_outflows(wallet_address):
    """Gathers all outbound activities safely from the consolidation wallet."""
    outflows = []

    print("[*] Checking Outbound USDC Transmissions...")
    usdc_txs = make_safe_request({
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

    print("[*] Checking Outbound Standard ETH Transmissions...")
    eth_txs = make_safe_request({
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

    print("[*] Checking Internal Smart Contract Executions...")
    internal_txs = make_safe_request({
        "module": "account", "action": "txlistinternal",
        "address": wallet_address, "startblock": START_BLOCK,
        "endblock": "99999999", "sort": "asc"
    })
    for tx in internal_txs:
        if tx['from'].lower() == wallet_address.lower() and int(tx['value']) > 0:
            outflows.append({
                "type": "INTERNAL Swap/Execution", "to": tx['to'],
                "amount": f"{int(tx['value']) / 10**18:.4f} ETH equivalent",
                "hash": tx['hash'], "time": tx['timeStamp']
            })

    outflows.sort(key=lambda x: int(x['time']))
    return outflows

def check_destination_info(address):
    """Checks if destination is a smart contract protocol or private wallet."""
    code = make_safe_request({"module": "proxy", "action": "eth_getCode", "address": address, "tag": "latest"})
    if code and code != "0x":
        return "Smart Contract Protocol (DEX/Bridge/Mixer)"
    return "Private Deposit/User Wallet Address"

def run_pivot_trace():
    print("="*80)
    print(f"TARGETED CONSOLIDATION TRACE: {CONSOLIDATION_WALLET}")
    print("="*80)
    
    outflows = get_pivot_outflows(CONSOLIDATION_WALLET)
    
    if not outflows:
        print("\n📍 STATUS: Funds appear stagnant or API returned zero valid outflows.")
        print("➡️ Action: Confirm block number or manually cross-check the address via Etherscan UI.")
        return

    print(f"\n✅ Found {len(outflows)} clear outbound movements after July 17th:\n")
    for tx in outflows:
        dest_type = check_destination_info(tx['to'])
        tx_time = datetime.fromtimestamp(int(tx['time'])).strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"➔ [{tx['type']}] Dispatched {tx['amount']}")
        print(f"  Destination: {tx['to']} ({dest_type})")
        print(f"  Timestamp:   {tx_time}")
        print(f"  Tx Hash:     {tx['hash']}\n")
        print("-" * 50)

if __name__ == "__main__":
    run_pivot_trace()
