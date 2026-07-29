import csv
from datetime import datetime
import time
import requests

# ---------------------------------------------------------------------------
# CORE DATA STRATEGIES (Your explicit inputs organized)
# ---------------------------------------------------------------------------
TARGET_ADDRESSES = [
    "bc1p22p5ywpdc4ptglryn4d8j2tzwg00ml5qd9aqaarnjekqpzj5rl3sqs93w9",  # Taproot (P2TR)
    "1Cm8gRoe3jCi9rBHGLwVHaiP7xtuZ2s4Y",  # Legacy (P2PKH)
    "1EdFX33jg2LQhZMFM381Rx8bcBhEHzfwT",  # Legacy (P2PKH)
    "bc1pzeupdkxtv2v0p86nyzugdzsv20fyl8v8t60umxnxfvzrrh2kdpws796r0d",  # Taproot (P2TR)
]

KNOWN_SCAM_HASHES = [
    "c35f8dd5898292dadac3251f479fe1b283028c7398f73587ae7cd635893b6f4d",
    "1aa96cd4747e6f2ec09a44c904182582038c55c9bbcc9416040a6e029bc2f42e",
    "ab490aa4d9c561db81925db4aeef6a7774ffe56f4ef65219f6a8eaacaaf2e7ca",
    "9dfad5cc35b6a3adcaa573749164e2eb8ba90b1011c7d1f7a4316512d3c0b3d8",
]

CSV_FILE = "bitcoin_scam_trace_log.csv"

# Broad categorization heuristics for mapping endpoints
# (Real-world intelligence relies on TxOut entity tags)
CEX_IDENTIFIERS = [
    "12t9YDPg",
    "1AnwXgJD",
    "3FHN9",
]  # Known cluster prefixes (Truncated representation)


def identify_entity_type(address):
  """Evaluates wallet structure to identify potential risk behaviors."""
  if address.startswith("bc1p"):
    return "Taproot (High Privacy / Script Capability)"
  elif address.startswith("bc1q"):
    return "Native SegWit (Standard Wallet)"
  elif address.startswith("1"):
    return "Legacy Wallet (Often CEX Deposit or Old Wallet)"
  return "Unknown Type"


def check_laundering_patterns(inputs_count, outputs_count, value_btc):
  """Flags common multi-hop peel chains or mixing signatures."""
  if inputs_count == 1 and outputs_count > 10:
    return "Peel Chain / Distribution (Laundering Red Flag)"
  if inputs_count > 5 and outputs_count <= 2:
    return "Consolidation (Gathering stolen funds)"
  if value_btc > 1.0:
    return "High Value Outflow - Urgent Priority"
  return "Standard Movement"


def trace_bitcoin_wallets():
  print(f"Initializing Trace on {len(TARGET_ADDRESSES)} target nodes...")

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
      # Using Blockchain.info open API endpoint
      url = f"https://blockchain.info{wallet}?limit=50"
      try:
        response = requests.get(url)
        if response.status_code != 200:
          print(f"Skipping {wallet}: API limit or invalid node.")
          continue

        data = response.json()
        txs = data.get("txs", [])

        for tx in txs:
          tx_hash = tx.get("hash")
          tx_time = datetime.fromtimestamp(tx.get("time", 0)).strftime(
              "%Y-%m-%d %H:%M:%S"
          )

          is_scam_hash_match = "YES" if tx_hash in KNOWN_SCAM_HASHES else "No"
          inputs_cnt = len(tx.get("inputs", []))
          outputs_cnt = len(tx.get("out", []))

          # Process outputs to trace where funds went from this wallet
          for output in tx.get("out", []):
            out_addr = output.get("addr")
            # Satoshis to BTC conversion
            value_btc = output.get("value", 0) / 100000000.0

            if out_addr and out_addr != wallet:
              w_type = identify_entity_type(out_addr)
              risk_notes = check_laundering_patterns(
                  inputs_cnt, outputs_cnt, value_btc
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

          # Process inputs to see how money arrived
          for inp in tx.get("inputs", []):
            prev_out = inp.get("prev_out", {})
            in_addr = prev_out.get("addr")
            value_btc = prev_out.get("value", 0) / 100000000.0

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
                  "Input Source",
                  is_scam_hash_match,
              ])

        time.sleep(2)  # Defensive throttling for public rate limits
      except Exception as e:
        print(f"Failed processing wallet {wallet}: {str(e)}")

  print(f"SUCCESS: Comparison complete. Check output: '{CSV_FILE}'")


if __name__ == "__main__":
  trace_bitcoin_wallets()
