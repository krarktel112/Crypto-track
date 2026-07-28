import os
import sys
import time
import datetime
import logging
import requests
from typing import Dict, List, Set, Tuple, Optional

# --- Rich Formatting for Progress & Dashboard Output ---
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.spinner import Spinner

console = Console()

# ==========================================
# CONFIGURATION & INITIAL SETUP
# ==========================================
ETHERSCAN_API_KEY = "ZFEQKMEBZ6T7NERFNZHEFM8NIE46HRHZ9A"
ETHERSCAN_BASE_URL = "https://api.etherscan.io/api"

STARTING_TX_HASHES = [
    "0x8274d085c74164f1f2a8e67b0ffeccd95a3c74e51c43d289de1a535d9bdb9ae0",
    "0x447ed6764b719bc3921f699e836a12d1394f6390d423a1c71c3e04cda731f217",
]

# Optional Alert Configs (Leave blank or set via environment variables to activate)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")  # e.g., "123456789:ABC..."
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")      # e.g., "@mychannel" or "1234567"

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER", "")

POLL_INTERVAL_SECONDS = 30  # Interval for continuous monitoring loop

# Known DEX Routers & Exchange Addresses (Database expander)
KNOWN_DEX_ROUTERS = {
    "0x7a250d5630b4cf539739df2c5dacb4c659f2488d": "Uniswap V2 Router",
    "0xe592427a0aece92de3edee1f18e0157c05861564": "Uniswap V3 Router",
    "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45": "Uniswap Universal Router",
    "0xd9e1ce17f2641f24ae83637ab66a2cca9c378804": "Sushiswap Router",
    "0x1111111254fb6c44bac0bed2854e76f90643097d": "1inch v5 Router",
    "0xdef1c0ded9bec7f1a1670819833240f027b25eff": "0x Exchange Router",
}

KNOWN_CEX_WALLETS = {
    "0x28c6c06298d514db089934071355e5743bf21d60": "Binance Hot Wallet 14",
    "0x21a31ee1afc51d94c2efccaa2092ad1028285549": "Binance Hot Wallet 1",
    "0x50310926a4b41200e77a28e35f37756dbdafb3b0": "Coinbase Deposit Wallet",
    "0x7160ec948a287c701f2f814d4850d57e8ebff575": "Kraken Hot Wallet",
    "0x0d0707963952f2a722999f17044806a57c281313": "OKX Hot Wallet",
}

# ==========================================
# NOTIFICATION SYSTEM
# ==========================================
def send_telegram_alert(message: str):
    """Sends notification to Telegram if credentials are set."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        console.print(f"[bold red]Failed to send Telegram alert:[/bold red] {e}")

def send_email_alert(subject: str, body: str):
    """Sends notification email via SMTP if credentials are set."""
    if not SMTP_USER or not SMTP_PASS or not EMAIL_RECEIVER:
        return
    import smtplib
    from email.mime.text import MIMEText

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = EMAIL_RECEIVER

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, [EMAIL_RECEIVER], msg.as_string())
    except Exception as e:
        console.print(f"[bold red]Failed to send Email alert:[/bold red] {e}")

def notify(title: str, text: str):
    """Unified alert handler."""
    msg = f"🚨 *{title}*\n\n{text}"
    send_telegram_alert(msg)
    send_email_alert(f"[Crypto Tracker Alert] {title}", text)

# ==========================================
# ETHERSCAN CLIENT & CLASSIFIER
# ==========================================
class EtherscanTracker:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.monitored_addresses: Set[str] = set()
        self.seen_tx_hashes: Set[str] = set()
        self.address_labels: Dict[str, str] = {}

    def _get(self, params: dict) -> dict:
        params["apikey"] = self.api_key
        res = requests.get(ETHERSCAN_BASE_URL, params=params, timeout=15)
        res.raise_for_status()
        return res.json()

    def classify_address(self, address: str) -> Tuple[str, str]:
        """
        Determines if an address is CEX, DEX, Smart Contract, or standard EOA.
        Returns: (type_label, detailed_name)
        """
        addr_lower = address.lower()

        if addr_lower in KNOWN_CEX_WALLETS:
            return "CEX", KNOWN_CEX_WALLETS[addr_lower]

        if addr_lower in KNOWN_DEX_ROUTERS:
            return "DEX", KNOWN_DEX_ROUTERS[addr_lower]

        # Check if address is a smart contract code
        params = {"module": "proxy", "action": "eth_getCode", "address": address}
        try:
            data = self._get(params)
            code = data.get("result", "0x")
            if code and code != "0x":
                # It is a Smart Contract, check source code info on Etherscan
                contract_info = self.get_contract_info(address)
                if contract_info:
                    name = contract_info.get("ContractName", "Unknown Contract")
                    if any(x in name.lower() for x in ["router", "swap", "pool", "vault", "pair"]):
                        return "DEX / DeFi Protocol", name
                    if any(x in name.lower() for x in ["binance", "coinbase", "kraken", "okx"]):
                        return "CEX", name
                    return "Smart Contract", name
                return "Smart Contract", "Unverified Contract"
        except Exception:
            pass

        return "EOA Wallet", "Personal Wallet"

    def get_contract_info(self, address: str) -> Optional[dict]:
        params = {"module": "contract", "action": "getsourcecode", "address": address}
        try:
            res = self._get(params)
            if res.get("status") == "1" and res.get("result"):
                return res["result"][0]
        except Exception:
            pass
        return None

    def get_transaction_details(self, tx_hash: str) -> Optional[dict]:
        """Fetches detailed information on a single transaction by hash."""
        params = {"module": "proxy", "action": "eth_getTransactionByHash", "txhash": tx_hash}
        tx_data = self._get(params).get("result")
        if not tx_data:
            return None

        # Receipt to check status and gas used
        params_receipt = {"module": "proxy", "action": "eth_getTransactionReceipt", "txhash": tx_hash}
        receipt = self._get(params_receipt).get("result", {})

        # Block timestamp
        block_num = tx_data.get("blockNumber")
        timestamp = "Unknown"
        if block_num:
            params_block = {"module": "block", "action": "getblockreward", "blockno": int(block_num, 16)}
            block_info = self._get(params_block).get("result")
            if block_info and "timeStamp" in block_info:
                ts = int(block_info["timeStamp"])
                timestamp = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')

        val_eth = int(tx_data.get("value", "0"), 16) / 1e18

        from_addr = tx_data.get("from", "").lower()
        to_addr = tx_data.get("to", "").lower() if tx_data.get("to") else "Contract Creation"

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

    def get_address_transactions(self, address: str) -> List[dict]:
        """Gets normal transactions for a monitored address."""
        params = {
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "page": 1,
            "offset": 20,
            "sort": "desc"
        }
        res = self._get(params)
        if res.get("status") == "1":
            return res.get("result", [])
        return []

# ==========================================
# MAIN TRACING & MONITORING ENGINE
# ==========================================
def run_tracker():
    tracker = EtherscanTracker(ETHERSCAN_API_KEY)

    console.print(Panel.fit("[bold green]Crypto Transaction Flow Tracker & Continuous Monitor[/bold green]", border_style="cyan"))

    # Step 1: Process starting transactions
    console.print("\n[bold yellow]Phase 1: Initial Hash Inspection & Chain Discovery[/bold yellow]")
    table = Table(title="Starting Transactions Summary")
    table.add_column("Tx Hash", style="dim", overflow="fold")
    table.add_column("From", style="cyan")
    table.add_column("To Target", style="magenta")
    table.add_column("Amount (ETH)", justify="right", style="green")
    table.add_column("Timestamp", style="yellow")

    for tx_hash in STARTING_TX_HASHES:
        with console.status(f"[bold cyan]Fetching details for {tx_hash[:10]}...[/bold cyan]"):
            details = tracker.get_transaction_details(tx_hash)

        if details:
            tracker.seen_tx_hashes.add(tx_hash.lower())
            tracker.monitored_addresses.add(details["to"].lower())

            table.add_row(
                details["tx_hash"][:12] + "...",
                f"{details['from'][:8]}...\n[{details['from_type']}]",
                f"{details['to'][:8]}...\n[{details['to_type']}]",
                f"{details['value_eth']:.4f}",
                details["timestamp"]
            )

            # Optional Alert on initial discovery
            notify(
                "Initial Seed Transaction Discovered",
                f"Tx: `{tx_hash}`\n"
                f"From: `{details['from']}` ({details['from_type']})\n"
                f"To: `{details['to']}` ({details['to_type']})\n"
                f"Amount: {details['value_eth']} ETH\n"
                f"Time: {details['timestamp']}"
            )

    console.print(table)
    console.print(f"\n[bold green]✓ Added {len(tracker.monitored_addresses)} recipient address(es) to real-time watchlist.[/bold green]")

    # Step 2: Continuous Real-Time Monitoring Loop
    console.print("\n[bold yellow]Phase 2: Continuous Monitoring Active[/bold yellow] (Press Ctrl+C to stop)\n")

    poll_count = 0
    try:
        while True:
            poll_count += 1
            now_str = datetime.datetime.now().strftime("%H:%M:%S")

            with console.status(f"[bold cyan]Poll #{poll_count} ({now_str}) | Checking {len(tracker.monitored_addresses)} addresses...[/bold cyan]") as status:
                for target_address in list(tracker.monitored_addresses):
                    tx_list = tracker.get_address_transactions(target_address)

                    for tx in tx_list:
                        tx_h = tx.get("hash", "").lower()
                        if tx_h in tracker.seen_tx_hashes:
                            continue

                        tracker.seen_tx_hashes.add(tx_h)

                        # Extract details
                        val_eth = int(tx.get("value", "0")) / 1e18
                        from_addr = tx.get("from", "").lower()
                        to_addr = tx.get("to", "").lower()
                        ts = int(tx.get("timeStamp", 0))
                        time_str = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')

                        from_type, _ = tracker.classify_address(from_addr)
                        to_type, _ = tracker.classify_address(to_addr)

                        # Print alert table
                        event_table = Table(title=f"🚨 NEW TRANSACTION DETECTED - Poll #{poll_count}", border_style="red")
                        event_table.add_column("Field", style="bold yellow")
                        event_table.add_column("Value", style="white")

                        event_table.add_row("Tx Hash", tx_h)
                        event_table.add_row("Monitored Subject", target_address)
                        event_table.add_row("From", f"{from_addr} [{from_type}]")
                        event_table.add_row("To", f"{to_addr} [{to_type}]")
                        event_table.add_row("Amount", f"{val_eth:.6f} ETH")
                        event_table.add_row("Timestamp", time_str)

                        console.print(event_table)

                        # Add new non-CEX destination addresses to watchlist
                        if to_addr and to_addr not in tracker.monitored_addresses and "CEX" not in to_type:
                            tracker.monitored_addresses.add(to_addr)
                            console.print(f"[bold magenta]➕ Expanded tracking graph to new destination address: {to_addr}[/bold magenta]")

                        # Send notification alert
                        notify(
                            "New Transaction Alert!",
                            f"Monitored Address: `{target_address}`\n"
                            f"Tx Hash: `{tx_h}`\n"
                            f"From: `{from_addr}` [{from_type}]\n"
                            f"To: `{to_addr}` [{to_type}]\n"
                            f"Amount: {val_eth:.6f} ETH\n"
                            f"Timestamp: {time_str}"
                        )

            time.sleep(POLL_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        console.print("\n[bold red]Monitoring stopped by user.[/bold red]")

if __name__ == "__main__":
    run_tracker()
