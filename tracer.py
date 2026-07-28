import sys
import time
import requests
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# CONFIGURATION & KNOWN ADDRESSES
# ==========================================
ETHERSCAN_API_KEY = "ZFEQKMEBZ6T7NERFNZHEFM8NIE46HRHZ9A"
TARGET_COMPARE_HASH = "0x8274d085c74164f1f2a8e67b0ffeccd95a3c74e51c43d289de1a535d9bdb9ae0"

# Telegram Configuration (Set enabled=True and fill credentials if desired)
TELEGRAM_CONFIG = {
    "enabled": False,
    "bot_token": "YOUR_TELEGRAM_BOT_TOKEN",
    "chat_id": "YOUR_TELEGRAM_CHAT_ID"
}

# Email Configuration (Set enabled=True and fill credentials if desired)
EMAIL_CONFIG = {
    "enabled": False,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "your_email@gmail.com",
    "sender_password": "your_app_password",
    "recipient_email": "recipient@gmail.com"
}

# Input Data Set provided for tracing
TRACKED_ITEMS = [
    {
        "type": "EVM",
        "tx_hash": "0x447ed6764b719bc3921f699e836a12d1394f6390d423a1c71c3e04cda731f217",
        "expected_amount": "1505$",
        "address": "0xb591b2a6382025d8a39c2ad8dfd4a88d422e4f14"
    },
    {
        "type": "BTC",
        "tx_hash": "c35f8dd5898292dadac3251f479fe1b283028c7398f73587ae7cd635893b6f4d",
        "expected_amount": "403.35",
        "address": "bc1p22p5ywpdc4ptglryn4d8j2tzwg00ml5qd9aqaarnjekqpzj5rl3sqs93w9"
    },
    {
        "type": "BTC",
        "tx_hash": "1aa96cd4747e6f2ec09a44c904182582038c55c9bbcc9416040a6e029bc2f42e",
        "expected_amount": "112.66",
        "address": "1Cm8gRoe3jCi9rBHGLwVHaiP7xtuZ2s4Y"
    },
    {
        "type": "BTC",
        "tx_hash": "ab490aa4d9c561db81925db4aeef6a7774ffe56f4ef65219f6a8eaacaaf2e7ca",
        "expected_amount": "1001",
        "address": "1EdFX33jg2LQhZMFM381Rx8bcBhEHzfwT"
    },
    {
        "type": "BTC",
        "tx_hash": "9dfad5cc35b6a3adcaa573749164e2eb8ba90b1011c7d1f7a4316512d3c0b3d8",
        "expected_amount": "N/A",
        "address": "bc1pzeupdkxtv2v0p86nyzugdzsv20fyl8v8t60umxnxfvzrrh2kdpws796r0d"
    },
    {
        "type": "EVM",
        "tx_hash": None,
        "expected_amount": None,
        "address": "0x675150eeec3cffa64d92d5d6ab5ab4cd4ef70633"
    }
]

# Database of notable DEX Routers & CEX Deposit/Hot Wallets
KNOWN_ENTITIES = {
    # DEX Routers
    "0x7a250d5630b4cf539739df2c5dacb4c659f2488d": "DEX (Uniswap V2 Router)",
    "0xe592427a0aece92de3edee1f18e0157c05861564": "DEX (Uniswap V3 Router)",
    "0x1111111254fb6c44bac0bed2854e76f90643097d": "DEX (1inch Router)",
    "0xd9e1ce17f2641f24ae83637ab66a2cca9c378804": "DEX (Sushiswap Router)",
    # Common CEX Wallets
    "0x28c6c06298d514db089934071355e5743bf21d60": "CEX (Binance Hot Wallet 14)",
    "0x21a31ee1afc51d94c2efccaa2092ad1028285549": "CEX (Binance Hot Wallet)",
    "0x70faa28a6b8d6829a4b1e629c2a47542ccc35070": "CEX (Coinbase)",
    "0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43": "CEX (Coinbase 10)",
}

# ==========================================
# NOTIFICATION ENGINE
# ==========================================
def send_telegram_alert(message: str):
    if not TELEGRAM_CONFIG["enabled"]:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_CONFIG['bot_token']}/sendMessage"
    payload = {"chat_id": TELEGRAM_CONFIG["chat_id"], "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"\n[!] Failed to send Telegram alert: {e}")

def send_email_alert(subject: str, message: str):
    if not EMAIL_CONFIG["enabled"]:
        return
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_CONFIG["sender_email"]
        msg["To"] = EMAIL_CONFIG["recipient_email"]
        msg["Subject"] = subject
        msg.attach(MIMEText(message, "plain"))

        server = smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"])
        server.starttls()
        server.login(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["sender_password"])
        server.sendmail(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["recipient_email"], msg.as_string())
        server.quit()
    except Exception as e:
        print(f"\n[!] Failed to send Email alert: {e}")

def notify_user(title: str, details: str):
    full_msg = f"🚨 *{title}*\n\n{details}"
    print(f"\n[ALERT SENT] {title}")
    send_telegram_alert(full_msg)
    send_email_alert(title, details)

# ==========================================
# CLASSIFICATION & API TRACING
# ==========================================
def classify_address(address: str, chain: str) -> str:
    """Identifies if an address is a CEX, DEX, or standard user wallet (EOA)."""
    if not address:
        return "Unknown"
    
    addr_lower = address.lower()
    if addr_lower in KNOWN_ENTITIES:
        return KNOWN_ENTITIES[addr_lower]
    
    if chain == "EVM":
        # Check if address is a Smart Contract on Ethereum
        url = f"https://api.etherscan.io/api?module=proxy&action=eth_getCode&address={address}&apikey={ETHERSCAN_API_KEY}"
        try:
            res = requests.get(url, timeout=5).json()
            code = res.get("result", "0x")
            if code != "0x" and len(code) > 2:
                return "DEX / Smart Contract"
            return "CEX Deposit Wallet or Standard User EOA"
        except Exception:
            return "EOA / Unclassified"
            
    elif chain == "BTC":
        if address.startswith("bc1p"):
            return "BTC Taproot Address (User/Service)"
        elif address.startswith("bc1q"):
            return "BTC Native SegWit Address"
        elif address.startswith("1") or address.startswith("3"):
            return "BTC Legacy Address"
    
    return "Standard EOA Wallet"

def fetch_evm_transaction(tx_hash: str):
    """Fetches details for an Ethereum transaction."""
    url = f"https://api.etherscan.io/api?module=proxy&action=eth_getTransactionByHash&txhash={tx_hash}&apikey={ETHERSCAN_API_KEY}"
    try:
        res = requests.get(url, timeout=10).json()
        result = res.get("result")
        if not result:
            return None
        
        # Calculate Value in ETH
        val_wei = int(result.get("value", "0x0"), 16)
        val_eth = val_wei / 10**18
        
        # Get timestamp by block
        block_num = result.get("blockNumber")
        timestamp = "Pending"
        if block_num:
            block_url = f"https://api.etherscan.io/api?module=block&action=getblockreward&blockno={int(block_num, 16)}&apikey={ETHERSCAN_API_KEY}"
            b_res = requests.get(block_url, timeout=5).json()
            raw_ts = b_res.get("result", {}).get("timeStamp")
            if raw_ts:
                timestamp = datetime.fromtimestamp(int(raw_ts)).strftime('%Y-%m-%d %H:%M:%S UTC')

        from_addr = result.get("from")
        to_addr = result.get("to")

        return {
            "tx_hash": tx_hash,
            "chain": "EVM",
            "from": from_addr,
            "from_type": classify_address(from_addr, "EVM"),
            "to": to_addr,
            "to_type": classify_address(to_addr, "EVM"),
            "value": f"{val_eth:.6f} ETH",
            "timestamp": timestamp,
            "block": block_num
        }
    except Exception as e:
        return {"error": str(e)}

def fetch_btc_transaction(tx_hash: str):
    """Fetches details for a Bitcoin transaction via Mempool.space."""
    url = f"https://mempool.space/api/tx/{tx_hash}"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code != 200:
            return None
        data = res.json()
        
        status = data.get("status", {})
        block_time = status.get("block_time")
        timestamp = datetime.fromtimestamp(block_time).strftime('%Y-%m-%d %H:%M:%S UTC') if block_time else "Unconfirmed"
        
        # Calculate total output amount in BTC
        total_sats = sum([out.get("value", 0) for out in data.get("vout", [])])
        total_btc = total_sats / 10**8

        inputs = [inp.get("prevout", {}).get("scriptpubkey_address") for inp in data.get("vin", []) if inp.get("prevout")]
        outputs = [out.get("scriptpubkey_address") for out in data.get("vout", []) if out.get("scriptpubkey_address")]

        from_addr = inputs[0] if inputs else "Unknown"
        to_addr = outputs[0] if outputs else "Unknown"

        return {
            "tx_hash": tx_hash,
            "chain": "BTC",
            "from": from_addr,
            "from_type": classify_address(from_addr, "BTC"),
            "to": to_addr,
            "to_type": classify_address(to_addr, "BTC"),
            "value": f"{total_btc:.6f} BTC",
            "timestamp": timestamp,
            "block": status.get("block_height", "Unconfirmed")
        }
    except Exception as e:
        return {"error": str(e)}

# ==========================================
# MONITORING & EXECUTION ENGINE
# ==========================================
def print_status_bar(iteration, total, prefix='', suffix='', length=30):
    """Displays terminal progress bar status."""
    percent = f"{100 * (iteration / float(total)):.1f}"
    filled_length = int(length * iteration // total)
    bar = '█' * filled_length + '-' * (length - filled_length)
    sys.stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix}')
    sys.stdout.flush()

def run_trace_and_monitor():
    print("\n=======================================================")
    print("      CRYPTO TRANSACTION TRACER & CONTINUOUS MONITOR    ")
    print("=======================================================\n")
    print(f"[*] Target Reference Hash to Match:\n    {TARGET_COMPARE_HASH}\n")
    
    seen_transactions = set()
    poll_count = 0

    try:
        while True:
            poll_count += 1
            timestamp_now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
            print(f"\n--- [Cycle #{poll_count} | {timestamp_now}] Scanning Transactions ---")
            
            total_items = len(TRACKED_ITEMS)
            
            for index, item in enumerate(TRACKED_ITEMS):
                print_status_bar(index + 1, total_items, prefix='Progress:', suffix='Checking...', length=25)
                
                tx_hash = item.get("tx_hash")
                if not tx_hash:
                    continue
                
                # Direct comparison with target hash
                is_target_match = (tx_hash.lower() == TARGET_COMPARE_HASH.lower())
                
                # Fetch Transaction Data
                if item["type"] == "EVM":
                    tx_data = fetch_evm_transaction(tx_hash)
                else:
                    tx_data = fetch_btc_transaction(tx_hash)
                
                if not tx_data or "error" in tx_data:
                    continue

                # Format Output Log
                log_output = (
                    f"\n\n[+] Hash: {tx_hash}\n"
                    f"    - Chain: {tx_data['chain']}\n"
                    f"    - Timestamp: {tx_data['timestamp']}\n"
                    f"    - Expected Input Amount: {item['expected_amount']}\n"
                    f"    - On-Chain Value: {tx_data['value']}\n"
                    f"    - Sender ({tx_data['from_type']}): {tx_data['from']}\n"
                    f"    - Recipient ({tx_data['to_type']}): {tx_data['to']}\n"
                    f"    - Target Hash Match: {'YES 🎯' if is_target_match else 'NO'}"
                )
                print(log_output)

                # Check if new transaction observed
                if tx_hash not in seen_transactions:
                    seen_transactions.add(tx_hash)
                    if is_target_match:
                        notify_user(
                            "TARGET TRANSACTION MATCH DETECTED",
                            f"Matched Target Tx: {tx_hash}\nAmount: {tx_data['value']}\nTimestamp: {tx_data['timestamp']}"
                        )
            
            print(f"\n\n[✓] Cycle #{poll_count} complete. Waiting 30 seconds for continuous monitoring (Press Ctrl+C to stop)...")
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n\n[!] Tracer stopped by user.")

if __name__ == "__main__":
    run_trace_and_monitor()
