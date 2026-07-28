def get_transaction_details(self, tx_hash: str) -> Optional[dict]:
    """Fetches detailed information on a single transaction by hash."""
    params = {"module": "proxy", "action": "eth_getTransactionByHash", "txhash": tx_hash}
    response = self._get(params)
    
    # Guard clause: ensure response is a dict and result is a valid dictionary
    if not isinstance(response, dict):
        console.print(f"[bold red]API returned invalid response for {tx_hash}: {response}[/bold red]")
        return None
        
    tx_data = response.get("result")
    
    # Etherscan returns string error messages (e.g., "Error! Invalid API Key")
    if not isinstance(tx_data, dict):
        console.print(f"[bold red]Could not fetch transaction {tx_hash}. Etherscan returned: {tx_data}[/bold red]")
        return None

    # Fetch block timestamp via RPC proxy eth_getBlockByNumber
    block_num = tx_data.get("blockNumber")
    timestamp = "Unknown"
    if block_num and isinstance(block_num, str):
        try:
            params_block = {
                "module": "proxy", 
                "action": "eth_getBlockByNumber", 
                "tag": block_num, 
                "boolean": "false"
            }
            block_res = self._get(params_block)
            block_info = block_res.get("result") if isinstance(block_res, dict) else None
            
            if isinstance(block_info, dict) and "timestamp" in block_info:
                ts = int(block_info["timestamp"], 16)
                timestamp = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        except Exception as e:
            console.print(f"[dim red]Could not resolve block timestamp: {e}[/dim red]")

    # Safe ETH Value conversion
    raw_val = tx_data.get("value")
    val_eth = int(raw_val, 16) / 1e18 if raw_val and raw_val != "0x" else 0.0

    from_addr = (tx_data.get("from") or "").lower()
    to_addr = (tx_data.get("to") or "").lower() if tx_data.get("to") else "Contract Creation"

    from_type, from_name = self.classify_address(from_addr)
    to_type, to_name = self.classify_address(to_addr) if to_addr != "Contract Creation" else ("Contract", "Creation")

    return {
        "tx_hash": tx_hash,
        "from": from_addr,
        "from_type": f"{from_type} ({from_name})",
        "to": to_addr,
        "to_type": f"{to_type} ({to_name})",
        "value_eth": val_eth,
        "timestamp": timestamp,
        "block_number": int(block_num, 16) if block_num else None
    }
