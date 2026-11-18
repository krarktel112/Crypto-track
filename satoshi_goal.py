import os
import time
import json
import calendar
from datetime import datetime
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
    "Package": 2.13,
    "Singles": 1.06,
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


def calculate_satoshi_goals():
    now = datetime.now()
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    current_day = now.day
    days_remaining = days_in_month - current_day

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
    print(f"Progress:   Day {current_day} of {days_in_month} ({days_remaining} left)")
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
            calculate_satoshi_goals()
            time.sleep(30)
            os.system('clear')
        except:
            print("restarting")
            time.sleep(30)
            os.system('clear')
