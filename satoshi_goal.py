import calendar
from datetime import datetime, timedelta
import json
import math
import os
import time
import requests

try:
  from coinbase.rest import RESTClient
except ImportError:
  RESTClient = None

# Monthly Expenses (USD)
EXPENSES = {
    "Rent": 863,
    "Utilities": 36.76,
    "Loan (Toget": 134.02,
    "Electric": 133.00,
    "Food": 121.08,
    "Personal / A": 80.00,
    "Pawn": 29.90,
    "Adderall": 15.00,
    "Zyprexa": 11.54,
    "Crunchyroll": 9.99,
    "Insurance": 6.50,
    "Celexa": 2.84,
    "Package": 0.31,
    "Single": 0.265,
}

# Next Package Tracker Config ($1.99 promo + 7% tax = $2.13)
NEXT_PACKAGE_USD = 2.13
SPREAD_BUFFER = 0.08  # 8% buffer for swap/card spread or rounding
FLEET_DAILY_SATS = 527.66  # Confirmed post-CloudMineX $1.99 Promo #1 rate
APP_CAP_SATS = 2500

# Coinbase CDP Auth & Local Cache Config
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CDP_KEY_FILE = os.path.join(BASE_DIR, "cdp_api_key.json")
CB_CACHE_FILE = os.path.join(BASE_DIR, "coinbase_sats_cache.json")
CB_REFRESH_SECONDS = 60  # Query authenticated Coinbase API at most once/min

# Manual non-Coinbase balances (update as you sweep)
SPEED_WALLET_SATS = 0
PENDING_APPS = {
    "btc_cloud_mining": {"balance": 0, "fee": 5},
}

SATS_PER_BTC = 100_000_000
FALLBACK_BTC_PRICE = 60240.68

_last_cb_fetch_ts = 0.0
_cached_cb_sats = 0
_cached_cb_status = "Init"


def _load_cached_coinbase_sats() -> tuple[int, str]:
  """Loads the last saved Coinbase BTC sats balance from disk."""
  if os.path.exists(CB_CACHE_FILE):
    try:
      with open(CB_CACHE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
      return int(data.get("coinbase_sats", 0)), "CB Cache"
    except Exception:
      pass
  return 0, "CB Unlinked"


def _save_cached_coinbase_sats(sats: int, btc_amount: float) -> None:
  """Persists the latest Coinbase BTC sats balance to disk."""
  try:
    with open(CB_CACHE_FILE, "w", encoding="utf-8") as f:
      json.dump(
          {
              "coinbase_sats": sats,
              "coinbase_btc": btc_amount,
              "updated_at": datetime.now().isoformat(),
          },
          f,
          indent=2,
      )
  except Exception:
    pass


def get_coinbase_btc_sats(force: bool = False) -> tuple[int, str]:
  """Fetches current available BTC balance in Satoshis via Coinbase CDP SDK."""
  global _last_cb_fetch_ts, _cached_cb_sats, _cached_cb_status

  now_ts = time.time()
  if (
      not force
      and _last_cb_fetch_ts > 0
      and (now_ts - _last_cb_fetch_ts) < CB_REFRESH_SECONDS
  ):
    return _cached_cb_sats, _cached_cb_status

  if RESTClient is None:
    sats, status = _load_cached_coinbase_sats()
    return sats, "No CDP SDK"

  try:
    if os.path.exists(CDP_KEY_FILE):
      client = RESTClient(key_file=CDP_KEY_FILE)
    else:
      # Falls back to COINBASE_API_KEY and COINBASE_API_SECRET env vars
      client = RESTClient()

    total_btc = 0.0
    cursor = None
    while True:
      resp = client.get_accounts(limit=250, cursor=cursor)
      accounts = (
          resp.get("accounts", [])
          if isinstance(resp, dict)
          else getattr(resp, "accounts", [])
      )
      for acct in accounts:
        currency = (
            acct.get("currency")
            if isinstance(acct, dict)
            else getattr(acct, "currency", "")
        )
        if currency == "BTC":
          avail = (
              acct.get("available_balance", {})
              if isinstance(acct, dict)
              else getattr(acct, "available_balance", {})
          )
          val = (
              avail.get("value", "0")
              if isinstance(avail, dict)
              else getattr(avail, "value", "0")
          )
          total_btc += float(val or 0.0)

      has_next = (
          resp.get("has_next", False)
          if isinstance(resp, dict)
          else getattr(resp, "has_next", False)
      )
      cursor = (
          resp.get("cursor")
          if isinstance(resp, dict)
          else getattr(resp, "cursor", None)
      )
      if not has_next or not cursor:
        break

    cb_sats = round(total_btc * SATS_PER_BTC)
    _save_cached_coinbase_sats(cb_sats, total_btc)
    _last_cb_fetch_ts = now_ts
    _cached_cb_sats = cb_sats
    _cached_cb_status = "CB Live"
    return cb_sats, "CB Live"

  except Exception:
    sats, status = _load_cached_coinbase_sats()
    _last_cb_fetch_ts = now_ts
    _cached_cb_sats = sats
    _cached_cb_status = status
    return sats, status


def get_live_btc_price() -> tuple[float, str]:
  """Fetches live BTC-USD spot price from Coinbase's public API."""
  try:
    resp = requests.get(
        "https://api.coinbase.com/v2/prices/BTC-USD/spot",
        timeout=10,
    )
    resp.raise_for_status()
    price = float(resp.json()["data"]["amount"])
    return price, "Coinbase Live"
  except Exception:
    return FALLBACK_BTC_PRICE, "Fallback Reference"


def usd_to_sats(usd_amount: float, btc_price: float) -> int:
  """Converts a USD dollar amount into whole Satoshis."""
  if btc_price <= 0:
    return 0
  return round((usd_amount / btc_price) * SATS_PER_BTC)


def print_next_package_tracker(
    btc_price: float,
    coinbase_sats: int,
    cb_status: str,
    speed_wallet_sats: int = SPEED_WALLET_SATS,
    pending_apps: dict[str, dict[str, int]] | None = None,
    daily_rate_sats: float = FLEET_DAILY_SATS,
    package_usd: float = NEXT_PACKAGE_USD,
    spread_buffer: float = SPREAD_BUFFER,
    cap_sats: int = APP_CAP_SATS,
) -> None:
  """Prints a 40-char progress tracker toward the next tax-inclusive package."""
  pending_apps = pending_apps if pending_apps is not None else PENDING_APPS

  net_pending = 0
  alerts = []
  for app_name, info in pending_apps.items():
    bal = info.get("balance", 0)
    fee = info.get("fee", 0)
    net_pending += max(0, bal - fee)

    if bal >= cap_sats * 0.85:
      alerts.append(f"{app_name}: {bal}/{cap_sats} near cap!")
    elif fee > 0 and bal > 0 and (fee / bal) > 0.01:
      alerts.append(f"{app_name}: {bal} ({fee}s fee = {fee/bal*100:.1f}%)")

  total_net_sats = coinbase_sats + speed_wallet_sats + net_pending

  sats_per_usd = SATS_PER_BTC / btc_price if btc_price > 0 else 0
  target_spot = math.ceil(package_usd * sats_per_usd)
  target_buf = math.ceil(target_spot * (1 + spread_buffer))

  need_spot = max(0, target_spot - total_net_sats)
  need_buf = max(0, target_buf - total_net_sats)

  days_spot = need_spot / daily_rate_sats if daily_rate_sats > 0 else 0.0
  days_buf = need_buf / daily_rate_sats if daily_rate_sats > 0 else 0.0

  now = datetime.now()
  eta_spot = now + timedelta(days=days_spot)
  eta_buf = now + timedelta(days=days_buf)

  pct = min(100.0, (total_net_sats / target_spot) * 100) if target_spot else 0.0
  bar_len = 20
  filled = int(round(bar_len * (pct / 100)))
  bar = "#" * filled + "-" * (bar_len - filled)

  print("=" * 40)
  print(f"  NEXT PACKAGE (${package_usd:.2f} W/ TAX)")
  print("=" * 40)
  print(f"Fleet Rate: {daily_rate_sats:.2f} sats/day")
  print(f"Coinbase:   {coinbase_sats:,} sats ({cb_status})")
  print(
      f"Net Stack:  {total_net_sats:,} sats"
      f" (SW:{speed_wallet_sats:,} P:{net_pending:,})"
  )
  print(f"Progress:   [{bar}] {pct:5.1f}%")
  print("-" * 40)
  print(f"Spot Goal:  {target_spot:,} sats")
  print(f"Remaining:  {need_spot:,} sats (~{days_spot:.1f}d)")
  print(f"ETA Spot:   {eta_spot.strftime('%b %d %I:%M%p')}")
  print("-" * 40)
  print(f"Buf (+{int(spread_buffer*100)}%): {target_buf:,} sats")
  print(f"Remaining:  {need_buf:,} sats (~{days_buf:.1f}d)")
  print(f"ETA Buf:    {eta_buf.strftime('%b %d %I:%M%p')}")
  if alerts:
    print("-" * 40)
    print("ALERTS:")
    for alert in alerts:
      print(f"! {alert[:37]}")
  print("=" * 40)


def calculate_satoshi_goals(
    btc_price: float | None = None, price_source: str | None = None
):
  now = datetime.now()
  days_in_month = calendar.monthrange(now.year, now.month)[1]
  current_day = now.day
  days_remaining = days_in_month - current_day

  if btc_price is None or price_source is None:
    btc_price, price_source = get_live_btc_price()
  sats_per_dollar = round(SATS_PER_BTC / btc_price)

  total_monthly_usd = sum(EXPENSES.values())
  daily_usd_needed = total_monthly_usd / days_in_month
  mtd_usd_target = daily_usd_needed * current_day

  total_monthly_sats = usd_to_sats(total_monthly_usd, btc_price)
  daily_sats_needed = round(total_monthly_sats / days_in_month)
  mtd_sats_target = daily_sats_needed * current_day

  # Mobile-friendly 40-char formatted output
  print("=" * 40)
  print(f"   SATOSHI EXPENSE GOAL ({now.strftime('%b %Y').upper()})")
  print("=" * 40)
  print(f"BTC Spot:   ${btc_price:,.2f} ({price_source})")
  print(f"Rate:       {sats_per_dollar:,} sats / $1.00")
  print(
      f"Progress:   Day {current_day} of {days_in_month} ({days_remaining}"
      " left)"
  )
  print("-" * 40)
  print("MONTHLY EXPENSE BREAKDOWN:")
  for name, cost in sorted(EXPENSES.items(), key=lambda x: x[1], reverse=True):
    item_sats = usd_to_sats(cost, btc_price)
    print(f"• {name:<13} ${cost:>6.2f} | {item_sats:>9,} sats")
  print("-" * 40)
  print(f"MONTHLY TOTAL:   ${total_monthly_usd:,.2f}")
  print(f"                 {total_monthly_sats:,} sats")
  print("-" * 40)
  print(f"DAILY GOAL:      ${daily_usd_needed:,.2f} / day")
  print(f"                 {daily_sats_needed:,} sats / day")
  print("-" * 40)
  print(f"DAY {current_day} TARGET:    ${mtd_usd_target:,.2f} earned")
  print(f"                 {mtd_sats_target:,} sats earned")
  print("=" * 40)


if __name__ == "__main__":
  while True:
    try:
      btc_price, price_source = get_live_btc_price()
      cb_sats, cb_status = get_coinbase_btc_sats()
      calculate_satoshi_goals(btc_price, price_source)
      print_next_package_tracker(btc_price, cb_sats, cb_status)
      time.sleep(30)
      os.system("clear")
    except Exception:
      print("restarting")
      time.sleep(30)
      os.system("clear")
