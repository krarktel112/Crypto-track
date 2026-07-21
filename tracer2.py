import requests

# Public free EVM RPC endpoint (Ethereum Mainnet)
RPC_URL = "https://eth.llamarpc.com"

# The EVM transaction hash
TX_HASH = "0x447ed6764b719bc3921f699e836a12d1394f6390d423a1c71c3e04cda731f217"

def get_rpc_data(method, params):
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(RPC_URL, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json().get("result")
    else:
        print(f"Error fetching {method}: {response.status_code}")
        return None

def trace_evm_transaction(tx_hash):
    tx_hash = tx_hash.strip().lower()
    print(f"=== Tracing EVM Transaction: {tx_hash} ===\n")

    # 1. Fetch main transaction details
    tx = get_rpc_data("eth_getTransactionByHash", [tx_hash])
    if not tx:
        print("[-] Transaction not found on Ethereum Mainnet. (If this was on BSC, Polygon, or Arbitrum, update RPC_URL).")
        return

    from_addr = tx.get("from")
    to_addr = tx.get("to")
    value_wei = int(tx.get("value", "0x0"), 16)
    value_eth = value_wei / 10**18

    print(f"Status: Found on-chain")
    print(f"From (Sender):    {from_addr}")
    print(f"To (Recipient):   {to_addr}")
    print(f"Native Value:     {value_eth:.6f} ETH\n")

    # 2. Fetch transaction receipt for execution status and ERC-20 event logs
    receipt = get_rpc_data("eth_getTransactionReceipt", [tx_hash])
    if receipt:
        status = "Success" if receipt.get("status") == "0x1" else "Failed"
        print(f"Execution Status: {status}")
        
        logs = receipt.get("logs", [])
        print(f"Total Event Logs: {len(logs)}")

        # ERC-20 Transfer Event signature hash: Transfer(address,address,uint256)
        TRANSFER_EVENT_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

        print("\n--- Token Transfers Detected (ERC-20 / ERC-721) ---")
        found_transfer = False
        for i, log in enumerate(logs):
            topics = log.get("topics", [])
            if topics and topics[0].lower() == TRANSFER_EVENT_TOPIC and len(topics) >= 3:
                found_transfer = True
                contract_address = log.get("address")
                # Strip zero-padding from indexed address topics
                token_from = "0x" + topics[1][-40:]
                token_to = "0x" + topics[2][-40:]
                
                # Raw value in hex
                raw_data = log.get("data", "0x0")
                raw_val = int(raw_data, 16) if raw_data != "0x" else 0

                print(f"  Log #{i}:")
                print(f"    Token Contract: {contract_address}")
                print(f"    From:           {token_from}")
                print(f"    To (End Wallet):{token_to}")
                print(f"    Raw Amount:     {raw_val}")

        if not found_transfer:
            print("  No ERC-20 token transfer events found in this receipt.")

if __name__ == "__main__":
    trace_evm_transaction(TX_HASH)
