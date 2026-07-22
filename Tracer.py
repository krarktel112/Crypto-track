import requests
import json
import asyncio
import websockets
from collections import deque

# Configuration
ETHERSCAN_API_KEY = "ZFEQKMEBZ6T7NERFNZHEFM8NIE46HRHZ9A"
BLOCKNATIVE_API_KEY = "YOUR_BLOCKNATIVE_API_KEY"
USDC_CONTRACT_ADDRESS = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48" # Ethereum Mainnet
START_WALLET = "0x466ba3edd0783b0e0e675b50e7e59396b0433064"
MAX_HOPS = 3 # Define how deep to trace the transaction tree

# Etherscan endpoint to fetch past transactions
ETHERSCAN_URL = f"https://etherscan.io{USDC_CONTRACT_ADDRESS}&address={{address}}&sort=desc&apikey={ETHERSCAN_API_KEY}"

def get_past_usdc_transfers(wallet_address):
    """Fetches past USDC transactions for a given wallet using Etherscan."""
    url = ETHERSCAN_URL.format(address=wallet_address)
    response = requests.get(url)
    data = response.json()
    
    transfers = []
    if data['status'] == '1':
        for tx in data['result']:
            transfers.append({
                "from": tx['from'].lower(),
                "to": tx['to'].lower(),
                "value": int(tx['value']) / 10**6, # USDC has 6 decimals
                "hash": tx['hash']
            })
    return transfers

def trace_wallet_hops(start_wallet, max_depth):
    """Recursively traces funds hopped across multiple wallets."""
    visited = set()
    queue = deque([(start_wallet.lower(), 0)])
    transaction_tree = []

    while queue:
        current_wallet, depth = queue.popleft()
        
        if depth >= max_depth:
            continue
            
        if current_wallet not in visited:
            visited.add(current_wallet)
            print(f"Tracing history for wallet: {current_wallet} at depth {depth}")
            
            transfers = get_past_usdc_transfers(current_wallet)
            
            for tx in transfers:
                tx['depth'] = depth
                transaction_tree.append(tx)
                
                # If we haven't reached max hops, add the receiving wallet to queue to trace further
                if tx['to'] not in visited:
                    queue.append((tx['to'], depth + 1))
                    
    return transaction_tree

async def monitor_mempool_realtime(wallet_address):
    """Monitors the Blocknative WebSocket API to catch real-time USDC hops."""
    uri = "wss://://blocknative.com"
    
    subscription_payload = {
        "timeStamp": "...",
        "dappId": BLOCKNATIVE_API_KEY,
        "version": "1",
        "blockchain": "ethereum",
        "network": "mainnet",
        "add": wallet_address.lower(),
        "filters": [
            {
                "contract": USDC_CONTRACT_ADDRESS,
                "event": "Transfer(address,address,uint256)"
            }
        ]
    }

    print(f"Listening for real-time USDC transactions for {wallet_address}...")
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps(subscription_payload))
        
        while True:
            response = await websocket.recv()
            event = json.loads(response)
            
            # Parse real-time transfer details
            if "transaction" in event:
                tx = event["transaction"]
                print("\n[!] NEW HOP DETECTED IN MEMPOOL:")
                print(f"From: {tx.get('from')}")
                print(f"To: {tx.get('to')}")
                print(f"Hash: {tx.get('hash')}")

def main():
    # 1. Trace past transaction hops
    print("--- Tracing Past USDC Transactions ---")
    history = trace_wallet_hops(START_WALLET, MAX_HOPS)
    
    print("\nTracing Complete. Found {len(history)} hops.")
    for hop in history:
        print(f"Depth {hop['depth']} | {hop['from']} -> {hop['to']} | {hop['value']} USDC")

    # 2. Start real-time monitoring
    asyncio.run(monitor_mempool_realtime(START_WALLET))

if __name__ == "__main__":
    main()
        if current_txid in visited_txids or hop > max_hops:
            continue

        visited_txids.add(current_txid)
        
        # 1. Get detailed info on the current transaction
        tx_data = get_transaction(current_txid)
        if not tx_data:
            continue

        indent = "  " * hop
        print(f"{indent}[Hop {hop}] Analyzing TxID: {current_txid}")

        # Print outputs (where the money was allocated in this TX)
        vouts = tx_data.get("vout", [])
        for i, vout in enumerate(vouts):
            address = vout.get("scriptpubkey_address", "Unknown/Script")
            value_sats = vout.get("value", 0)
            value_btc = value_sats / 100_000_000
            print(f"{indent}  ├── Output #{i}: {value_btc:.8f} BTC -> Address: {address}")

        # 2. Check which outputs have been spent downstream
        outspends = get_outspends(current_txid)
        if outspends:
            for i, spend_info in enumerate(outspends):
                if spend_info.get("spent"):
                    next_txid = spend_info.get("txid")
                    print(f"{indent}  └── Output #{i} spent in Next TxID: {next_txid}")
                    
                    # Queue next hop if within depth limit
                    if hop + 1 <= max_hops:
                        queue.append((next_txid, hop + 1))
                else:
                    print(f"{indent}  └── Output #{i} remains UNSPENT (Funds sitting at address)")

        print("")
        # Respect rate limits for public API calls
        time.sleep(0.5)

if __name__ == "__main__":
    # Replace with your actual starting Transaction ID (TxID)
    STARTING_TXID = "0x447ed6764b719bc3921f699e836a12d1394f6390d423a1c71c3e04cda731f217"
    
    # Trace up to 3 hops downstream
    trace_funds(start_txid=STARTING_TXID, max_hops=3)
