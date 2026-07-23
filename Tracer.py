import requests
import time
from datetime import datetime

# Configuration
API_KEY = "ZFEQKMEBZ6T7NERFNZHEFM8NIE46HRHZ9A"
CONSOLIDATION_WALLET = "0x220fe14412bca438b3dbc5078e04f802f8f098e7"
USDC_CONTRACT = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"

# Target block approximate for mid-July 2026 to ignore older background noise
START_BLOCK = "20315000" 
BASE_URL = "https://etherscan.io"

def make_request(params):
    """Executes safe API calls against Etherscan."""
    time.sleep(0.25)
    params["apikey"] = API_KEY
    try:
        response = requests.get(BASE_URL, params=params)
        data = response.json()
        if data.get("status") == "1":
            return data.get("result", [])
    except Exception as e:
        print(f"    ⚠️ Etherscan API Error: {e}")
    return []

def get_pivot_outflows(wallet_address):
    """Gathers all outbound activities from the consolidation wallet."""
    outflows = []

    # 1. Check Outbound USDC
    usdc_txs = make_request({
        "module": "account", "action": "tokentx",
        "contractaddress": USDC_CONTRACT, "address": wallet_address,
        "startblock": START_BLOCK, "endblock": "99999999", "sort": "asc"
    })
    for tx in usdc_txs:
        if tx['from'].lower() == wallet_address.lower():
            outflows.append({
                "type": "USDC Token",
                "to": tx['to'],
                "amount": f"{int(tx['value']) / 10**6:,.2f} USDC",
                "hash": tx['hash'],
                "time": tx['timeStamp']
            })

    # 2. Check Outbound ETH
    eth_txs = make_request({
        "module": "account", "action": "txlist",
        "address": wallet_address, "startblock": START_BLOCK,
        "endblock": "99999999", "sort": "asc"
    })
    for tx in eth_txs:
        if tx['from'].lower() == wallet_address.lower() and int(tx['value']) > 0:
            outflows.append({
                "type": "Standard ETH",
                "to": tx['to'],
                "amount": f"{int(tx['value']) / 10**18:.4f} ETH",
                "hash": tx['hash'],
                "time": tx['timeStamp']
            })

    # 3. Check Internal Contract Outflows (DeFi Swaps/Bridges)
    internal_txs = make_request({
        "module": "account", "action": "txlistinternal",
        "address": wallet_address, "startblock": START_BLOCK,
        "endblock": "99999999", "sort": "asc"
    })
    for tx in internal_txs:
        if tx['from'].lower() == wallet_address.lower() and int(tx['value']) > 0:
            outflows.append({
                "type": "INTERNAL Swap/Execution",
                "to": tx['to'],
                "amount": f"{int(tx['value']) / 10**18:.4f} ETH equivalent",
                "hash": tx['hash'],
                "time": tx['timeStamp']
            })

    outflows.sort(key=lambda x: int(x['time']))
    return outflows

def check_destination_info(address):
    """Checks if the destination address is a known smart contract or exchange footprint."""
    code = make_request({"module": "proxy", "action": "eth_getCode", "address": address, "tag": "latest"})
    if code and code != "0x":
        source = make_request({"module": "contract", "action": "getsourcecode", "address": address})
        if source and isinstance(source, list) and "ContractName" in source[0]:
            return f"Smart Contract Protocol [{source[0]['ContractName']}]"
        return "Smart Contract (Unverified Protocol)"
    return "Private Deposit/User Wallet Address"

def run_pivot_trace():
    print("="*80)
    print(f"TARGETED CONSOLIDATION TRACE: {CONSOLIDATION_WALLET}")
    print("="*80)
    
    outflows = get_pivot_outflows(CONSOLIDATION_WALLET)
    
    if not outflows:
        print("📍 STATUS: Funds are currently sitting stagnant in this third wallet.")
        print("➡️ Action: Set up an alert; the scammer hasn't moved the consolidated loot yet.")
        return

    print(f"Found {len(outflows)} outbound movements from this hub after July 17th:\n")
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
