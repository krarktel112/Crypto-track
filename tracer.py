import csv
from datetime import datetime
import time
import requests

# ---------------------------------------------------------------------------
# DATA RECOVERY CONFIGURATION (Case-preserved input strings)
# ---------------------------------------------------------------------------
TARGET_ADDRESSES = [
    "bc1p22p5ywpdc4ptglryn4d8j2tzwg00ml5qd9aqaarnjekqpzj5rl3sqs93w9",
    "1Cm8gRoe3jCi9rBHGLwVHaiP7xtuZ2s4Y",
    "1EdFX33jg2LQhZMFM381Rx8bcBhEHzfwT",
    "bc1pzeupdkxtv2v0p86nyzugdzsv20fyl8v8t60umxnxfvzrrh2kdpws796r0d",
]

KNOWN_SCAM_HASHES = [
    "c35f8dd5898292dadac3251f479fe1b283028c7398f73587ae7cd635893b6f4d",
    "1aa96cd4747e6f2ec09a44c904182582038c55c9bbcc9416040a6e029bc2f42e",
    "ab490aa4d9c561db81925db4aeef6a7774ffe56f4ef65219f6a8eaacaaf2e7ca",
    "9dfad5cc35b6a3adcaa573749164e2eb8ba90b1011c7d1f7a4316512d3c0b3d8",
]

CSV_FILE = "bitcoin_scam_trace_log.csv"


def identify_entity_type(address):
  if address.startswith("bc1p"):
    return "Taproot (High Privacy / Complex Script)"
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
  print(f"Connecting to Mempool Engine to evaluate {len(TARGET_ADDRESSES)} nodes...")

  with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
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

    for wallet in TARGET_ADDRESSES:
      # Mempool API retains precise capitalization formatting required for Bech32 strings
      url = f"https://mempool.space{wallet}/txs"
      try:
        response = requests.get(url)
        if response.status_code != 200:
          print(f"Skipping {wallet}: Server error code {response.status_code}")
          continue

        txs = response.json()
        print(f"Processing {len(txs)} transactions found for: {wallet}")

        for tx in txs:
          tx_hash = tx.get("txid")
          is_scam_hash_match = "YES" if tx_hash in KNOWN_SCAM_HASHES else "No"

          # Extract Unix timestamp from block header info
          status = tx.get("status", {})
          block_time = status.get("block_time", 0)
          tx_time = (
              datetime.fromtimestamp(block_time).strftime("%Y-%m-%d %H:%M:%S")
              if block_time
              else "Unconfirmed / Pending"
          )

          inputs = tx.get("vin", [])
          outputs = tx.get("vout", [])

          # 1. Evaluate Incoming Path Transactions
          for inp in inputs:
            prevout = inp.get("prevout", {})
            in_addr = prevout.get("scriptpubkey_address")
            value_btc = prevout.get("value", 0) / 100000000.0

            if in_addr and in_addr != wallet:
              w_type = identify_entity_type(in_addr)
              writer.writerow([
                  wallet,
                  tx_time,
                  tx_hash,
                  "INBOUND",
                  in_addr,
                  value_btc,
                  w_type,
                  "Source Input Node",
                  is_scam_hash_match,
              ])

          # 2. Evaluate Outgoing Path Transactions
          for out in outputs:
            out_addr = out.get("scriptpubkey_address")
            value_btc = out.get("value", 0) / 100000000.0

            if out_addr and out_addr != wallet:
              w_type = identify_entity_type(out_addr)
              risk_notes = check_laundering_patterns(
                  len(inputs), len(outputs), value_btc
              )

              writer.writerow([
                  wallet,
                  tx_time,
                  tx_hash,
                  "OUTBOUND",
                  out_addr,
                  value_btc,
                  w_type,
                  risk_notes,
                  is_scam_hash_match,
              ])

        time.sleep(1)  # Rate limiting compliance for the free tier public endpoint
      except Exception as e:
        print(f"Critical error mapping node {wallet}: {str(e)}")

  print(f"\nSUCCESS: Processing Complete. Output saved to '{CSV_FILE}'")


if __name__ == "__main__":
  trace_bitcoin_wallets()
