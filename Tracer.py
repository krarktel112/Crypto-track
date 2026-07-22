import requests
from datetime import datetime
import time

# Configuration
ETHERSCAN_API_KEY = "ZFEQKMEBZ6T7NERFNZHEFM8NIE46HRHZ9A"
USDC_CONTRACT = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
START_WALLET = "0x466ba3edd0783b0e0e675b50e7e59396b0433064"

# Target date window configuration
START_DATE_STR = "2026-07-07 00:00:00"  # Format: YYYY-MM-DD HH:MM:SS
MAX_HOPS = 3 

# Free-tier local registry of prominent CEX deposit/hot wallets
CEX_REGISTRY = {
    "0x28c6c06298d514db089934071355e5743bf21d60": "Binance: Hot Wallet",
    "0xdfd5293d8e347dfe59e90efd55b2956a1343963d": "Binance: Deposit",
    "0xddfabcdc4d8ffc6d5beaf154f18b778f892a0740": "Paxful: Hot Wallet",
    "0x477b8d5ef7c2c42b82d4e989343a60a77f3a6192": "Kraken: Hot Wallet",
    "0x5038289369932c4a85641747ef02213e9a785d03": "Coinbase: Hot Wallet",
    "0x71660c4005ba85c37ccec51a014902af3f6e1f0e": "OKX: Deposit Wallet",
    "0xa7efae728d2936e78bda97dc267687568dd593f3": "Crypto.com: Hot Wallet",
}

def date_to_unix(date_string):
    """Converts a UTC date string into a Unix timestamp."""
    dt = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
    return int(time.mktime(dt.timetuple()))

def get_outbound_hops(wallet_address, start_timestamp, end_timestamp):
    """Fetches outbound-only USDC transfers within the requested date window using Etherscan API."""
    url = (
        f"https://etherscan.io"
        f"&contractaddress={USDC_CONTRACT}&address={wallet_address}"
        f"&sort=asc&apikey={ETHERSCAN_API_KEY}"
    )
    
    try:
        response = requests.get(url)
        data = response.json()
    except Exception as e:
        print(f"Network error tracing {wallet_address}: {e}")
        return []

    outbound_transfers = []
    
    if data.get('status') == '1' and isinstance(data.get('result'), list):
        for tx in data['result']:
            tx_timestamp = int(tx['timeStamp'])
            tx_from = tx['from'].lower()
            
            # Restrict window: Must be after start date, before current execution time, and outbound
            if start_timestamp <= tx_timestamp <= end_timestamp and tx_from == wallet_address.lower():
                outbound_transfers.append({
                    "from": tx_from,
                    "to": tx['to'].lower(),
                    "value": int(tx['value']) / 10**6,  # 6 decimal places for USDC
                    "hash": tx['hash'],
                    "timestamp": tx_timestamp,
                    "date": datetime.fromtimestamp(tx_timestamp).strftime('%Y-%m-%d %H:%M:%S')
                })
                
    return outbound_transfers

def trace_outbound_tree(current_wallet, start_timestamp, end_timestamp, current_depth, max_depth, visited=None):
    """Recursively traces cascading outbound transfers and flags CEX matches."""
    if visited is None:
        visited = set()
        
    if current_depth >= max_depth or current_wallet in visited:
        return
        
    visited.add(current_wallet)
    print(f"\n[Depth {current_depth}] Scanning outbound hops for: {current_wallet}")
    
    # Check if the current wallet itself is a known CEX
    if current_wallet in CEX_REGISTRY:
        print(f"🛑 TARGET TERMINATED: Address matches known endpoint -> {CEX_REGISTRY[current_wallet]}")
        return

    # Etherscan free tier safety delay
    time.sleep(0.25) 
    
    hops = get_outbound_hops(current_wallet, start_timestamp, end_timestamp)
    
    for hop in hops:
        destination = hop['to']
        cex_tag = f"⚠️ [CEX DETECTED: {CEX_REGISTRY[destination]}]" if destination in CEX_REGISTRY else "[Private Wallet]"
        
        print(f"   ↳ HOP DETECTED: {hop['date']} | Out to: {destination} {cex_tag} | Amount: {hop['value']} USDC")
        
        # Keep cascading the timeline window forward 
        trace_outbound_tree(destination, hop['timestamp'], end_timestamp, current_depth + 1, max_depth, visited)

def main():
    target_start_timestamp = date_to_unix(START_DATE_STR)
    target_end_timestamp = int(time.time())  # Automatically fetches exact current Unix time execution epoch
    
    current_date_str = datetime.fromtimestamp(target_end_timestamp).strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"Starting CEX-Aware Outbound Tracker from Origin: {START_WALLET}")
    print(f"Tracking interval: {START_DATE_STR} to {current_date_str}\n")
    
    trace_outbound_tree(START_WALLET, target_start_timestamp, target_end_timestamp, current_depth=0, max_depth=MAX_HOPS)

if __name__ == "__main__":
    main()
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
