import os
import csv
import time
import smtplib
from datetime import datetime, timezone
from email.mime.text import MIMEText
import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# ==============================================================================
# CONFIGURATION
# ==============================================================================

ETHERSCAN_API_KEY = "ZFEQKMEBZ6T7NERFNZHEFM8NIE46HRHZ9A"
ETHERSCAN_BASE_URL = "https://api.etherscan.io/api"
CSV_FILE_PATH = "crypto_trace_log.csv"

STARTING_TXS = [
    "0x8274d085c74164f1f2a8e67b0ffeccd95a3c74e51c43d289de1a535d9bdb9ae0",
    "0x447ed6764b719bc3921f699e836a12d1394f6390d423a1c71c3e04cda731f217"
]

# --- NOTIFICATION CONFIGURATION ---
ENABLE_TELEGRAM = False
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"

ENABLE_EMAIL = False
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "your_email@gmail.com"
SENDER_PASSWORD = "your_app_password"
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

CSV_HEADERS = [
    "timestamp",
    "tx_hash",
    "from",
    "from_type",
    "to",
    "to_type",
    "to_label",
    "amount_eth",
    "block"
]

console = Console()

# ==============================================================================
# NOTIFICATION ENGINE
# ==============================================================================

def send_telegram_alert(message: str):
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
    text = f"🚨 *Crypto Trace Alert: {event_title}*\n\n{details}"
    send_telegram_alert(text)
    send_email_alert(f"Crypto Trace Alert: {event_title}", details)

# ==============================================================================
# BLOCKCHAIN ANALYZER & CONTINUOUS CSV LOGGING
# ==============================================================================

class CryptoTracer:
    def __init__(self, api_key: str, csv_filepath: str = CSV_FILE_PATH):
        self.api_key = api_key
        self.csv_filepath = csv_filepath
        self.processed_txs = set()
        self.trace_history = []
        self._ensure_csv_header()

    def _ensure_csv_header(self):
        """Creates the CSV file with column headers if it does not exist yet."""
        if not os.path.exists(self.csv_filepath):
            try:
                with open(self.csv_filepath, mode="w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(CSV_HEADERS)
            except Exception as e:
                console.print(f"[bold red]Failed to initialize CSV file {self.csv_filepath}: {e}[/bold red]")

    def append_to_csv(self, record: dict):
        """Appends a single transaction record to the CSV file immediately."""
        try:
            with open(self.csv_filepath, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    record.get("timestamp"),
                    record.get("tx_hash"),
                    record.get("from"),
                    record.get("from_type", {}).get("type", "Unknown"),
                    record.get("to"),
                    record.get("to_type", {}).get("type", "Unknown"),
                    record.get("to_type", {}).get("label", "N/A"),
                    record.get("amount_eth"),
                    record.get("block")
                ])
                f.flush()
        except Exception as e:
            console.print(f"[bold red]Failed to append record to CSV: {e}[/bold red]")

    def load_state_from_csv(self) -> bool:
        """Reads existing CSV log on startup to avoid processing duplicates."""
        if not os.path.exists(self.csv_filepath):
            return False

        try:
            with open(self.csv_filepath, mode="r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    tx_hash = row.get("tx_hash")
                    if not tx_hash:
                        continue
                    
                    self.processed_txs.add(tx_hash)
                    
                    to_addr = row.get("to", "")
                    to_type = row.get("to_type", "EOA")
                    to_label = row.get("to_label", "External Wallet")
                    from_addr = row.get("from", "")
                    from_type = row.get("from_type", "EOA")

                    rec = {
                        "timestamp": row.get("timestamp"),
                        "tx_hash": tx_hash,
                        "from": from_addr,
                        "from_type": {"type": from_type, "label": "External Wallet"},
                        "to": to_addr,
                        "to_type": {"type": to_type, "label": to_label},
                        "amount_eth": float(row.get("amount_eth", 0.0)),
                        "block": row.get("block")
                    }
                    self.trace_history.append(rec)
                    count += 1

            if count > 0:
                console.print(f"[bold green]📂 Loaded {count} prior transaction(s) from {self.csv_filepath}[/bold green]\n")
                return True
        except Exception as e:
            console.print(f"[bold red]Error reading existing CSV {self.csv_filepath}: {e}[/bold red]")
        return False

    def classify_address(self, address: str) -> dict:
        addr_lower = address.lower()
        if addr_lower in KNOWN_CEX_ADDRESSES:
            return {"type": "CEX", "label": KNOWN_CEX_ADDRESSES[addr_lower]}
        if addr_lower in KNOWN_DEX_ROUTERS:
            return {"type": "DEX", "label": KNOWN_DEX_ROUTERS[addr_lower]}
        
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
        params = {
            "module": "proxy",
            "action": "eth_getTransactionByHash",
            "txhash": tx_hash,
            "apikey": self.api_key
        }
        try:
            res = requests.get(ETHERSCAN_BASE_URL, params=params, timeout=10).json()
        except Exception as e:
            console.print(f"[bold red]HTTP Error for {tx_hash[:10]}: {e}[/bold red]")
            return None

        result = res.get("result")
        if not result or not isinstance(result, dict):
            error_msg = result if isinstance(result, str) else res.get("message", "Unknown error")
            console.print(f"[bold yellow]⚠️ API Warning for {tx_hash[:10]}...: {error_msg}[/bold yellow]")
            return None

        value_hex = result.get("value", "0x0") or "0x0"
        value_wei = int(value_hex, 16)
        value_eth = value_wei / 10**18

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

    def execute_trace(self, starting_hashes: list):
        """Processes the target transactions once."""
        with console.status("[bold green]⚙️ Working: Fetching transaction details & classifying entities...", spinner="dots"):
            for tx_hash in starting_hashes:
                if tx_hash in self.processed_txs:
                    continue

                tx_data = self.get_tx_details(tx_hash)
                if tx_data:
                    self.processed_txs.add(tx_hash)
                    self.trace_history.append(tx_data)
                    self.append_to_csv(tx_data)

                    alert_msg = (
                        f"Hash: `{tx_hash[:10]}...`\n"
                        f"From: `{tx_data['from']}` ({tx_data['from_type']['type']})\n"
                        f"To: `{tx_data['to']}` ({tx_data['to_type']['type']} - {tx_data['to_type']['label']})\n"
                        f"Amount: {tx_data['amount_eth']:.4f} ETH\n"
                        f"Time: {tx_data['timestamp']}"
                    )
                    trigger_alerts("Transaction Traced", alert_msg)
                    time.sleep(0.3)

# ==============================================================================
# UI DISPLAY & EXECUTION
# ==============================================================================

def render_dashboard(tracer: CryptoTracer) -> Table:
    title_text = "💎 Crypto Trace Dashboard | Status: [bold cyan]TRACE COMPLETE[/bold cyan]"
    table = Table(title=title_text, expand=True)

    table.add_column("Timestamp", style="cyan", no_wrap=True)
    table.add_column("Tx Hash", style="bold yellow")
    table.add_column("From", style="magenta")
    table.add_column("To Target", style="green")
    table.add_column("Entity Type", style="bold magenta")
    table.add_column("Amount (ETH)", justify="right", style="bold green")

    for item in tracer.trace_history:
        dest_type = item['to_type']['type']
        
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
    tracer = CryptoTracer(ETHERSCAN_API_KEY, CSV_FILE_PATH)

    # 1. Load existing state if available
    tracer.load_state_from_csv()
    
    # 2. Run trace
    tracer.execute_trace(STARTING_TXS)

    # 3. Output results and exit cleanly
    console.clear()
    console.print(render_dashboard(tracer))
    console.print(Panel(
        f"[bold green]✅ Trace completed successfully![/bold green]\n"
        f"Processed Transactions: {len(tracer.processed_txs)}\n"
        f"Results saved to: '{CSV_FILE_PATH}'",
        title="Execution Summary"
    ))

if __name__ == "__main__":
    main()
