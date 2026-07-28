import os
import time
import smtplib
from datetime import datetime, timezone
from email.mime.text import MIMEText
import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout

# ==============================================================================
# CONFIGURATION
# ==============================================================================

ETHERSCAN_API_KEY = "ZFEQKMEBZ6T7NERFNZHEFM8NIE46HRHZ9A"
ETHERSCAN_BASE_URL = "https://api.etherscan.io/api"

STARTING_TXS = [
    "0x8274d085c74164f1f2a8e67b0ffeccd95a3c74e51c43d289de1a535d9bdb9ae0",
    "0x447ed6764b719bc3921f699e836a12d1394f6390d423a1c71c3e04cda731f217"
]

# --- NOTIFICATION CONFIGURATION ---
# Set to True to enable notifications
ENABLE_TELEGRAM = False
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"

ENABLE_EMAIL = False
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "your_email@gmail.com"
SENDER_PASSWORD = "your_app_password"  # Use App Password for Gmail
RECIPIENT_EMAIL = "recipient@example.com"

# --- KNOWN ADDRESS DIRECTORY (CEX & DEX) ---
KNOWN_CEX_ADDRESSES = {
    "0x28c6c06298d514db089934071355e5743bf21d60": "Binance 14",
    "0x21a31ee1afc51d94c2efccaa3c09400018200614": "Binance 15",
    "0xdfd5293d8e347dfe59e90efd55b2956a1343963d": "Binance 16",
    "0x5033290db7efb663663613a077465f1a54016a24": "Binance 17",
    "0x71660c4005ba85c37ccec55d0c4493e66fe775d3": "Coinbase Hot Wallet 1",
    "0xa097a64312f473644b004f2fc1231fdf76b7e704": "Coinbase Hot Wallet 2",
    "0xda9dfa130df4de4673b89022ee50ff26f6ea73cf": "Kraken Hot Wallet 1",
    "0x2910043131f846f016d251642875150a00d11122": "OKX Hot Wallet",
    "0x0d0707963952f2a77299380901e12762a45a643b": "Bybit Hot Wallet",
}

KNOWN_DEX_ROUTERS = {
    "0x7a250d5630b4cf539739df2c5dacb4c659f2488d": "Uniswap v2 Router",
    "0xe592427a0aece92de3edee1f18e0157c05861564": "Uniswap v3 Router",
    "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45": "Uniswap Universal Router",
    "0xd9e1ce17f2641f24ae83637ab66a2cca9c378804": "SushiSwap Router",
    "0x1111111254fb6c44bac0bed2854e76f90643097d": "1inch v5 Router",
    "0xdef1c0dedd75f123304367564d3f3f338d3bead2": "0x Exchange Proxy",
    "0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad": "Uniswap Universal Router 2",
}

console = Console()

# ==============================================================================
# NOTIFICATION ENGINE
# ==============================================================================

def send_telegram_alert(message: str):
    """Send an alert message via Telegram Bot API."""
    if not ENABLE_TELEGRAM:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
    except Exception as e:
        console.print(f"[bold red]Failed to send Telegram alert:[/bold red] {e}")

def send_email_alert(subject: str, message: str):
    """Send an alert email via SMTP."""
    if not ENABLE_EMAIL:
        return
    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECIPIENT_EMAIL

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
    except Exception as e:
        console.print(f"[bold red]Failed to send Email alert:[/bold red] {e}")

def trigger_alerts(event_title: str, details: str):
    """Dispatches alerts across enabled channels."""
    text = f"🚨 *Crypto Trace Alert: {event_title}*\n\n{details}"
    send_telegram_alert(text)
    send_email_alert(f"Crypto Trace Alert: {event_title}", details)

# ==============================================================================
# BLOCKCHAIN ANALYZER
# ==============================================================================

class CryptoTracer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.monitored_addresses = set()
        self.processed_txs = set()
        self.trace_history = []

    def classify_address(self, address: str) -> dict:
        """Classifies address as CEX, DEX, Smart Contract, or Standard Wallet."""
        addr_lower = address.lower()
        
        if addr_lower in KNOWN_CEX_ADDRESSES:
            return {"type": "CEX", "label": KNOWN_CEX_ADDRESSES[addr_lower]}
        if addr_lower in KNOWN_DEX_ROUTERS:
            return {"type": "DEX", "label": KNOWN_DEX_ROUTERS[addr_lower]}
        
        # Query Etherscan to check if the address is a Smart Contract
        params = {
            "module": "contract",
            "action": "getabi",
            "address": address,
            "apikey": self.api_key
        }
        try:
            res = requests.get(ETHERSCAN_BASE_URL, params=params, timeout=10).json()
            if res.get("status") == "1":
                return {"type": "Contract/DEX", "label": "Smart Contract"}
        except Exception:
            pass

        return {"type": "EOA", "label": "External Wallet"}

    def get_tx_details(self, tx_hash: str) -> dict:
        """Fetch transaction info by tx hash."""
        params = {
            "module": "proxy",
            "action": "eth_getTransactionByHash",
            "txhash": tx_hash,
            "apikey": self.api_key
        }
        res = requests.get(ETHERSCAN_BASE_URL, params=params, timeout=10).json()
        result = res.get("result")
        if not result:
            return None

        # Convert hex value to ETH
        value_wei = int(result.get("value", "0x0"), 16)
        value_eth = value_wei / 10**18

        # Fetch block details for timestamp
        block_number = result.get("blockNumber")
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        if block_number:
            b_params = {
                "module": "block",
                "action": "getblockreward",
                "blockno": int(block_number, 16),
                "apikey": self.api_key
            }
            b_res = requests.get(ETHERSCAN_BASE_URL, params=b_params, timeout=10).json()
            if b_res.get("result", {}).get("timeStamp"):
                ts_int = int(b_res["result"]["timeStamp"])
                timestamp = datetime.fromtimestamp(ts_int, timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        to_addr = result.get("to") or "Contract Creation"
        to_classification = self.classify_address(to_addr) if to_addr != "Contract Creation" else {"type": "Contract", "label": "Creation"}
        from_classification = self.classify_address(result.get("from", ""))

        return {
            "tx_hash": tx_hash,
            "from": result.get("from"),
            "from_type": from_classification,
            "to": to_addr,
            "to_type": to_classification,
            "amount_eth": value_eth,
            "timestamp": timestamp,
            "block": int(block_number, 16) if block_number else "Pending"
        }

    def fetch_outgoing_txs(self, address: str) -> list:
        """Fetch normal outgoing transactions for an address."""
        params = {
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "page": 1,
            "offset": 50,
            "sort": "desc",
            "apikey": self.api_key
        }
        try:
            res = requests.get(ETHERSCAN_BASE_URL, params=params, timeout=10).json()
            if res.get("status") == "1" and isinstance(res.get("result"), list):
                # Filter outgoing transactions only
                return [tx for tx in res["result"] if tx.get("from", "").lower() == address.lower()]
        except Exception as e:
            console.print(f"[red]Error fetching transactions for {address}: {e}[/red]")
        return []

    def initialize_trace(self, starting_hashes: list):
        """Processes starting transactions and registers receivers for monitoring."""
        console.print("[bold blue]🔎 Initializing Crypto Transaction Trace...[/bold blue]\n")
        
        for tx_hash in starting_hashes:
            if tx_hash in self.processed_txs:
                continue

            tx_data = self.get_tx_details(tx_hash)
            if tx_data:
                self.processed_txs.add(tx_hash)
                self.trace_history.append(tx_data)

                # Add destination address to monitoring pool if it's an EOA wallet
                dest = tx_data["to"]
                if tx_data["to_type"]["type"] in ["EOA", "Contract/DEX"]:
                    self.monitored_addresses.add(dest.lower())

                alert_msg = (
                    f"Hash: `{tx_hash[:10]}...`\n"
                    f"From: `{tx_data['from']}` ({tx_data['from_type']['type']})\n"
                    f"To: `{tx_data['to']}` ({tx_data['to_type']['type']} - {tx_data['to_type']['label']})\n"
                    f"Amount: {tx_data['amount_eth']:.4f} ETH\n"
                    f"Time: {tx_data['timestamp']}"
                )
                trigger_alerts("Seed Transaction Detected", alert_msg)
                time.sleep(0.3)  # Rate limiting compliance

    def poll_new_transactions(self):
        """Scans monitored addresses for any new outgoing transfers."""
        new_events = False
        addresses_to_scan = list(self.monitored_addresses)

        for addr in addresses_to_scan:
            txs = self.fetch_outgoing_txs(addr)
            for tx in txs:
                tx_hash = tx.get("hash")
                if tx_hash in self.processed_txs:
                    continue

                value_eth = int(tx.get("value", 0)) / 10**18
                ts_int = int(tx.get("timeStamp", time.time()))
                formatted_ts = datetime.fromtimestamp(ts_int, timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

                to_addr = tx.get("to", "")
                to_class = self.classify_address(to_addr)
                from_class = self.classify_address(addr)

                record = {
                    "tx_hash": tx_hash,
                    "from": addr,
                    "from_type": from_class,
                    "to": to_addr,
                    "to_type": to_class,
                    "amount_eth": value_eth,
                    "timestamp": formatted_ts,
                    "block": tx.get("blockNumber")
                }

                self.processed_txs.add(tx_hash)
                self.trace_history.append(record)
                new_events = True

                # If recipient is a new wallet, follow it recursively
                if to_class["type"] in ["EOA"]:
                    self.monitored_addresses.add(to_addr.lower())

                alert_msg = (
                    f"New Downstream Transfer Detected!\n"
                    f"Hash: `{tx_hash[:10]}...`\n"
                    f"From: `{addr}`\n"
                    f"To: `{to_addr}` ({to_class['type']} - {to_class['label']})\n"
                    f"Amount: {value_eth:.4f} ETH\n"
                    f"Time: {formatted_ts}"
                )
                trigger_alerts("Downstream Movement Detected", alert_msg)
            
            time.sleep(0.2)  # Rate limiting safety

        return new_events

# ==============================================================================
# UI DISPLAY & MONITORING LOOP
# ==============================================================================

def render_dashboard(tracer: CryptoTracer, status_msg: str) -> Table:
    """Renders a rich table status view for terminal output."""
    table = Table(title="💎 Crypto Transaction Trace & Active Monitoring Dashboard", expand=True)

    table.add_column("Timestamp", style="cyan", no_wrap=True)
    table.add_column("Tx Hash", style="bold yellow")
    table.add_column("From", style="magenta")
    table.add_column("To Target", style="green")
    table.add_column("Entity Type", style="bold magenta")
    table.add_column("Amount (ETH)", justify="right", style="bold green")

    for item in tracer.trace_history[-12:]:  # Display last 12 traces
        dest_type = item['to_type']['type']
        
        # Color coding entity types
        if dest_type == "CEX":
            type_styled = f"[bold red]CEX ({item['to_type']['label']})[/bold red]"
        elif "DEX" in dest_type:
            type_styled = f"[bold yellow]DEX ({item['to_type']['label']})[/bold yellow]"
        else:
            type_styled = f"[blue]Wallet ({item['to_type']['label']})[/blue]"

        table.add_row(
            item['timestamp'],
            f"{item['tx_hash'][:8]}...{item['tx_hash'][-6:]}",
            f"{item['from'][:6]}...{item['from'][-4:]}",
            f"{item['to'][:6]}...{item['to'][-4:]}" if item['to'] else "N/A",
            type_styled,
            f"{item['amount_eth']:.4f} ETH"
        )

    return table

def main():
    tracer = CryptoTracer(ETHERSCAN_API_KEY)

    # Step 1: Initialize trace on starting hashes
    tracer.initialize_trace(STARTING_TXS)

    console.print(f"\n[bold green]✅ Initial trace complete. Now monitoring {len(tracer.monitored_addresses)} address(es) live...[/bold green]\n")
    time.sleep(2)

    # Step 2: Continuous monitoring loop
    poll_interval = 12  # Seconds between polls (~Ethereum block time)
    counter = 0

    try:
        while True:
            counter += 1
            status_text = f"Polling loop #{counter} | Monitored Addresses: {len(tracer.monitored_addresses)} | Processed Txs: {len(tracer.processed_txs)}"
            
            tracer.poll_new_transactions()
            
            console.clear()
            console.print(render_dashboard(tracer, status_text))
            console.print(Panel(f"[bold cyan]{status_text}[/bold cyan]  (Press Ctrl+C to exit)", title="Status"))

            time.sleep(poll_interval)
    except KeyboardInterrupt:
        console.print("\n[bold red]🛑 Monitoring stopped by user.[/bold red]")

if __name__ == "__main__":
    main()
