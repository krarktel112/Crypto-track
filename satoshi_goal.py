import calendar
from datetime import datetime, timedelta
import math
import os
import time
import requests

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
    "Packages": 2.13,
    "Singles": 1.06,
    "Package": 0.31,
    "Single": 0.265,
}

# Next Package Tracker Config (update balances/rates as you sweep & buy)
NEXT_PACKAGE_USD = 1.99
SPREAD_BUFFER = 0.08  # 8% buffer for swap/card spread or rounding
FLEET_DAILY_SATS = 527.66  # Confirmed post-CloudMineX $1.99 Promo #1 rate
APP_CAP_SATS = 2500

COINBASE_SATS = 0
SPEED_WALLET_SATS = 0
PENDING_APPS = {
    "btc_cloud_mining": {"balance": 0, "fee": 5},
}

SATS_PER_BTC = 100_000_000
FALLBACK_BTC_PRICE = 64963.39  # Live spot reference ($64,963.39)


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
    coinbase_sats: int = COINBASE_SATS,
    speed_wallet_sats: int = SPEED_WALLET_SATS,
    pending_apps: dict[str, dict[str, int]] | None = None,
    daily_rate_sats: float = FLEET_DAILY_SATS,
    package_usd: float = NEXT_PACKAGE_USD,
    spread_buffer: float = SPREAD_BUFFER,
    cap_sats: int = APP_CAP_SATS,
) -> None:
  """Prints a 40-char progress tracker toward the next package purchase."""
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
  print(f"   NEXT PACKAGE TRACKER (${package_usd:.2f})")
  print("=" * 40)
  print(f"Fleet Rate: {daily_rate_sats:.2f} sats/day")
  print(
      f"Net Stack:  {total_net_sats:,} sats"
      f" (CB:{coinbase_sats:,} SW:{speed_wallet_sats:,} P:{net_pending:,})"
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


def calculate_satoshi_goals(btc_price: float | None = None, price_source: str | None = None):
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
      calculate_satoshi_goals(btc_price, price_source)
      print_next_package_tracker(btc_price)
      time.sleep(30)
      os.system("clear")
    except Exception:
      print("restarting")
      time.sleep(30)
      os.system("clear")
