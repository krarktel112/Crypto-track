import requests
import time

# Configuration
API_KEY = "ZFEQKMEBZ6T7NERFNZHEFM8NIE46HRHZ9A"
BASE_URL = "https://etherscan.io"

def get_outgoing_transactions(wallet_address):
    """
    Fetches the outbound ETH transactions for a given wallet address.
    """
    params = {
        "module": "account",
        "action": "txlist",
        "address": wallet_address,
        "startblock": 0,
        "endblock": 99999999,
        "page": 1,
        "offset": 100,  # Number of transactions to return
        "sort": "desc", # Newest first
        "apikey": API_KEY
    }
    
    try:
        response = requests.get(BASE_URL, params=params)
        data = response.json()
        
        if data["status"] == "1" and data["message"] == "OK":
            tx_list = data["result"]
            outgoing_txs = []
            
            for tx in tx_list:
                # Filter for transactions originating FROM the watched wallet
                if tx["from"].lower() == wallet_address.lower():
                    # Convert value from Wei to Ether
                    ether_value = float(tx["value"]) / 10**18
                    outgoing_txs.append({
                        "to": tx["to"],
                        "value_eth": ether_value,
                        "hash": tx["hash"],
                        "block": tx["blockNumber"],
                        "time": time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(int(tx["timeStamp"])))
                    })
            return outgoing_txs
        else:
            print(f"API Error for {wallet_address}: {data.get('result', 'Unknown error')}")
            return []
            
    except Exception as e:
        print(f"Request failed: {e}")
        return []

# Target addresses to investigate
wallets_to_trace = [
    "0x675150eeec3cffa64d92d5d6ab5ab4cd4ef70633",
    "0xb591b2a6382025d8a39c2ad8dfd4a88d422e4f14",
    "0x220fe14412bca438b3dbc5078e04f802f8f098e7"
]

for wallet in wallets_to_trace:
    print(f"\n--- Scanning Outbound Transfers from: {wallet} ---")
    transactions = get_outgoing_transactions(wallet)
    
    if not transactions:
        print("No outgoing transactions found or error occurred.")
        continue
        
    for tx in transactions:
        if tx["value_eth"] > 0: # Focus on transfers carrying value
            print(f"Sent {tx['value_eth']:.4f} ETH to {tx['to']} on {tx['time']}")
            print(f"Tx Hash: {tx['hash']}\n")
