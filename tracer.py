def get_tx_details(self, tx_hash: str) -> dict:
        """Fetch transaction info by tx hash with robust error handling."""
        params = {
            "module": "proxy",
            "action": "eth_getTransactionByHash",
            "txhash": tx_hash,
            "apikey": self.api_key
        }
        try:
            response = requests.get(ETHERSCAN_BASE_URL, params=params, timeout=10)
            res = response.json()
        except Exception as e:
            console.print(f"[bold red]HTTP Request Error for {tx_hash[:10]}: {e}[/bold red]")
            return None

        result = res.get("result")

        # Handle API errors or missing transactions (e.g., rate limit string or invalid key)
        if not result or not isinstance(result, dict):
            error_msg = result if isinstance(result, str) else res.get("message", "Unknown error")
            console.print(f"[bold yellow]⚠️ API Warning for {tx_hash[:10]}...: {error_msg}[/bold yellow]")
            return None

        # Convert hex value to ETH safely
        value_hex = result.get("value", "0x0") or "0x0"
        value_wei = int(value_hex, 16)
        value_eth = value_wei / 10**18

        # Fetch block details for timestamp
        block_number = result.get("blockNumber")
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        
        if block_number and block_number != "0x0":
            b_params = {
                "module": "block",
                "action": "getblockreward",
                "blockno": int(block_number, 16),
                "apikey": self.api_key
            }
            try:
                b_res = requests.get(ETHERSCAN_BASE_URL, params=b_params, timeout=10).json()
                if isinstance(b_res.get("result"), dict) and b_res["result"].get("timeStamp"):
                    ts_int = int(b_res["result"]["timeStamp"])
                    timestamp = datetime.fromtimestamp(ts_int, timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            except Exception:
                pass

        to_addr = result.get("to")
        if not to_addr:
            to_addr = "Contract Creation"
            to_classification = {"type": "Contract", "label": "Creation"}
        else:
            to_classification = self.classify_address(to_addr)

        from_classification = self.classify_address(result.get("from", ""))

        return {
            "tx_hash": tx_hash,
            "from": result.get("from", "Unknown"),
            "from_type": from_classification,
            "to": to_addr,
            "to_type": to_classification,
            "amount_eth": value_eth,
            "timestamp": timestamp,
            "block": int(block_number, 16) if block_number else "Pending"
        }
