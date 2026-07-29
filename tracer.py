import csv
from datetime import datetime
import time
import requests

# ---------------------------------------------------------------------------
# CORE DATA SET
# ---------------------------------------------------------------------------
TARGET_ADDRESSES = [
    "bc1p22p5ywpdc4ptglryn4d8j2tzwg00ml5qd9aqaarnjekqpzj5rl3sqs93w9",
    "1Cm8gRoe3jCi9rBHGLwVHaiP7xtuZ2s4Y",
    "1EdFX33jg2LQhZMFM381Rx8bcBhEHzfwT",
    "bc1pzeupdkxtv2v0p86nyzugdzsv20fyl8v8t60umxnxfvzrrh2kdpws796r0d"
]

KNOWN_SCAM_HASHES = [
    "c35f8dd5898292dadac3251f479fe1b283028c7398f73587ae7cd635893b6f4d",
    "1aa96cd4747e6f2ec09a44c904182582038c55c9bbcc9416040a6e029bc2f42e",
    "ab490aa4d9c561db81925db4aeef6a7774ffe56f4ef65219f6a8eaacaaf2e7ca",
    "9dfad5cc35b6a3adcaa573749164e2eb8ba90b1011c7d1f7a4316512d3c0b3d8"
]

# TRACING DEPTH CONFIGURATION
# Depth 1: Traces just the target addresses.
# Depth 2: Collects all addresses targets paid out to, and traces those too.
MAX_DEPTH = 2 

CSV_FILE = "bitcoin_scam_trace_log.csv"
INTERTWINE_FILE = "wallet_intertwinement_report.csv"


def identify_entity_type(address):
    if not address:
        return "Unknown Node"
    if address.startswith("bc1p"):
        return "Taproot (High Privacy / Complex Script / DEX / Mixer Hub)"
    elif address.startswith("bc1q"):
        return "Native SegWit (Standard Wallet)"
    elif address.startswith("1"):
        return "Legacy (Often Exchange Deposit / Cold Wallet)"
    elif address.startswith("3"):
        return "Nested SegWit (Multi-Sig or Exchange)"
    return "Unknown Node"


def check_laundering_patterns(inputs_count, outputs_count, value_btc):
    if inputs_count == 1 and outputs_count > 8:
        return "Peel Chain Flag (Obfuscation / Splitting)"
    if inputs_count > 6 and outputs_count <= 2:
        return "Consolidation Flag (Sweeping Funds)"
    if value_btc > 0.5:
        return "High Value Outflow - Priority Node"
    return "Standard Hop"


def trace_bitcoin_wallets():
    print("Initializing Multi-Hop Mempool Engine...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    # Tracking sets to manage recursive flows
    queue_to_trace = [(addr, 1) for addr in TARGET_ADDRESSES]  # (address, current_depth)
    processed_wallets = set()
    
    # Structure to find intertwinement: {counterparty_address: [set_of_wallets_that_interacted_with_it]}
    counterparty_map = {}

    with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Trace_Depth",
            "Analyzed_Target",
            "Timestamp",
            "TxHash",
            "Direction",
            "Counterparty_Address",
            "Value_BTC",
            "Counterparty_Type",
            "Laundering_Indicators",
            "Match_Known_Scam_Hash",
        ])

        # Execute breadth-first crawl of the blockchain ledger
        while queue_to_trace:
            wallet, depth = queue_to_trace.pop(0)
            
            if wallet in processed_wallets:
                continue
            if depth > MAX_DEPTH:
                continue

            processed_wallets.add(wallet)
            print(f"\n[Depth {depth}] Mapping: {wallet}")

            base_url = "https://mempool.space"
            endpoint = f"/api/address/{wallet}/txs"
            full_url = base_url + endpoint

            try:
                response = requests.get(full_url, headers=headers, timeout=15)

                if response.status_code != 200:
                    print(f"   Skipping: HTTP Error {response.status_code}")
                    continue

                txs = response.json()
                print(f"   Pulled {len(txs)} transactions.")

                for tx in txs:
                    tx_hash = tx.get("txid")
                    is_scam_hash_match = "YES" if tx_hash in KNOWN_SCAM_HASHES else "No"

                    status = tx.get("status", {})
                    block_time = status.get("block_time", 0)
                    tx_time = (
                        datetime.fromtimestamp(block_time).strftime("%Y-%m-%d %H:%M:%S")
                        if block_time else "Unconfirmed / Pending"
                    )

                    inputs = tx.get("vin", [])
                    outputs = tx.get("vout", [])

                    # 1. Map Inbound Sources
                    for inp in inputs:
                        prevout = inp.get("prevout", {})
                        if prevout:
                            in_addr = prevout.get("scriptpubkey_address")
                            value_btc = prevout.get("value", 0) / 100000000.0

                            if in_addr and in_addr != wallet:
                                w_type = identify_entity_type(in_addr)
                                writer.writerow([
                                    depth, wallet, tx_time, tx_hash, "INBOUND",
                                    in_addr, value_btc, w_type, "Source Input Node",
                                    is_scam_hash_match
                                ])
                                
                                # Track intertwinement linkages
                                if in_addr not in counterparty_map:
                                    counterparty_map[in_addr] = set()
                                counterparty_map[in_addr].add(wallet)

                    # 2. Map Outbound Destinations & Queue Discoveries
                    for out in outputs:
                        out_addr = out.get("scriptpubkey_address")
                        value_btc = out.get("value", 0) / 100000000.0

                        if out_addr and out_addr != wallet:
                            w_type = identify_entity_type(out_addr)
                            risk_notes = check_laundering_patterns(
                                len(inputs), len(outputs), value_btc
                            )

                            writer.writerow([
                                depth, wallet, tx_time, tx_hash, "OUTBOUND",
                                out_addr, value_btc, w_type, risk_notes,
                                is_scam_hash_match
                            ])

                            # Track intertwinement linkages
                            if out_addr not in counterparty_map:
                                counterparty_map[out_addr] = set()
                            counterparty_map[out_addr].add(wallet)

                            # Dynamic Discovery: Add new address to queue for next depth level execution
                            if out_addr not in processed_wallets and depth < MAX_DEPTH:
                                queue_to_trace.append((out_addr, depth + 1))

                time.sleep(1)  # Protective anti-rate limiting delay
                
            except Exception as e:
                print(f"   Error mapping node {wallet}: {str(e)}")

    # ---------------------------------------------------------------------------
    # INTERTWINEMENT CROSS-REFERENCE LOGGING
    # ---------------------------------------------------------------------------
    print(f"\nAnalyzing intersections and writing intertwinement report...")
    with open(INTERTWINE_FILE, mode="w", newline="", encoding="utf-8") as f_int:
        int_writer = csv.writer(f_int)
        int_writer.writerow([
            "Shared_Counterparty_Address", 
            "Connected_Wallet_Count", 
            "Linked_Investigated_Wallets"
        ])
        
        shared_nodes_found = 0
        for node, connected_wallets in counterparty_map.items():
            # If more than 1 wallet from our trace history connects to this node, they intertwine
            if len(connected_wallets) > 1:
                int_writer.writerow([
                    node, 
                    len(connected_wallets), 
                    ", ".join(list(connected_wallets))
                ])
                shared_nodes_found += 1
                
    print(f"SUCCESS: Processing Complete.")
    print(f"➡️ Primary Trace Log generated: '{CSV_FILE}'")
    print(f"➡️ Intertwinement Map ({shared_nodes_found} intersections found): '{INTERTWINE_FILE}'")


if __name__ == "__main__":
    trace_bitcoin_wallets()
