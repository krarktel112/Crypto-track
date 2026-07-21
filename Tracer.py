import requests
import time

MEMPOOL_API_BASE = "https://mempool.space/api"

def get_transaction(txid):
    """Fetch details for a transaction by TxID."""
    url = f"{MEMPOOL_API_BASE}/tx/{txid}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"[-] Error fetching transaction {txid}: {response.status_code}")
        return None

def get_outspends(txid):
    """Fetch spending status for all outputs of a transaction."""
    url = f"{MEMPOOL_API_BASE}/tx/{txid}/outspends"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"[-] Error fetching outspends for {txid}: {response.status_code}")
        return None

def trace_funds(start_txid, max_hops=5):
    """
    Recursively traces funds starting from a given Bitcoin TxID up to max_hops.
    """
    print(f"=== Starting Fund Trace for TxID: {start_txid} ===\n")
    queue = [(start_txid, 0)]  # (txid, current_hop_level)
    visited_txids = set()

    while queue:
        current_txid, hop = queue.pop(0)

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
