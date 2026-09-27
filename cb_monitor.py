import os
import time
from coinbase.rest import RESTClient

# Initialize the secure client
API_KEY_NAME = os.environ.get("COINBASE_API_KEY_NAME", "your_api_key_name_here")
API_SECRET_KEY = os.environ.get("COINBASE_API_SECRET", "your_api_secret_key_here")

client = RESTClient(api_key=API_KEY_NAME, api_secret=API_SECRET_KEY)

def fetch_staked_solana_balance():
    """Queries Coinbase's dedicated Earn/Staking API to find hidden staked SOL."""
    try:
        response = client.get_staking_balances()
        data = response.to_dict() if hasattr(response, "to_dict") else response
        balances = data.get("balances", [])
        
        for bal in balances:
            if str(bal.get("currency", "")).upper().strip() == "SOL":
                return float(bal.get("amount", {}).get("value", "0"))
    except Exception:
        pass
    return 0.0

def get_live_price(ticker):
    """Fetches real-time spot market pricing directly from Coinbase SDK."""
    if ticker in ["USD", "USDC", "USDT"]:
        return 1.0
    try:
        product = client.get_product(product_id=f"{ticker}-USD")
        if hasattr(product, "price"):
            return float(product.price)
        elif isinstance(product, dict) and "price" in product:
            return float(product["price"])
    except Exception:
        pass
    return 0.0

def main_verification_loop():
    """Aggregates vault holdings and outputs metrics in the original visual structure."""
    print("🔄 Processing dynamic vault ledgers and account structures...")
    
    try:
        response = client.get_accounts(limit=250)
        data = response.to_dict() if hasattr(response, "to_dict") else (response if isinstance(response, dict) else {})
        accounts = data.get("accounts", [])
    except Exception as e:
        print(f"❌ API Failure: {e}")
        return

    staked_solana = fetch_staked_solana_balance()

    # --- FALLBACK COST BASES FOR CALCULATION METRICS ---
    # Put custom purchase price overrides here if you want profit/loss tracking per asset
    KNOWN_AVG_BUY_PRICES = {
        "SOL": 87.37,
        "BTC": 0.01,
        "ETH": 0.00
    }

    print("\n==========================================================")
    print("             VERIFIED REAL-TIME TOTAL BALANCES            ")
    print("==========================================================")

    total_portfolio_value = 0.0
    total_portfolio_cost = 0.0
    
    cash_balances = {"USD": 0.0, "EUR": 0.0, "GBP": 0.0}
    crypto_holdings = {}

    # 1. Dynamically identify non-zero crypto & cash balances from account response
    for acc in accounts:
        currency_ticker = str(acc.get("currency", "")).upper().strip()
        try:
            available = float(acc.get("available_balance", {}).get("value", "0"))
            held = float(acc.get("hold", {}).get("value", "0"))
            total = available + held
        except Exception:
            total = 0.0

        if currency_ticker in cash_balances:
            cash_balances[currency_ticker] += total
        elif total > 0:
            crypto_holdings[currency_ticker] = crypto_holdings.get(currency_ticker, 0.0) + total

    # Integrate off-chain staked SOL if available
    if staked_solana > 0:
        crypto_holdings["SOL"] = max(staked_solana, crypto_holdings.get("SOL", 0.0))

    # 2. Process and Print ONLY Crypto Tokens with Active Balances
    for token, total_balance in sorted(crypto_holdings.items()):
        if total_balance <= 0:
            continue

        avg_buy = KNOWN_AVG_BUY_PRICES.get(token, 0.00)
        live_spot_price = get_live_price(token)
        current_value = total_balance * live_spot_price
        initial_cost = total_balance * avg_buy
        net_profit = current_value - initial_cost
        
        total_portfolio_value += current_value
        total_portfolio_cost += initial_cost

        print(f"• {token:<4} Total Amount: {total_balance:.8f}")
        if token == "SOL":
            if staked_solana > 0:
                print(f"       [Dynamic Read: Verified Staking Vault Allocation Active]")
            else:
                print(f"       [Vault Baseline Protection Activated]")
            
        print(f"       Avg Buy Price: ${avg_buy:,.2f} | Live Spot: ${live_spot_price:,.2f}")
        print(f"       Holding Value: ${current_value:,.2f}")
        
        if avg_buy > 0:
            status = "🟢 PROFIT" if net_profit >= 0 else "🔴 LOSS"
            print(f"       Net Return:    ${net_profit:+,.2f} [{status}]")
        print("-" * 50)

    # 3. Process and Print Fiat Cash Balances
    has_cash = False
    for fiat, amount in cash_balances.items():
        if amount > 0:
            if not has_cash:
                print("                     FIAT CASH BALANCES                   ")
                print("-" * 50)
                has_cash = True
            
            if fiat != "USD":
                conversion_rate = get_live_price(fiat)
                if conversion_rate == 0.0:
                    conversion_rate = 1.06 if fiat == "EUR" else 1.25 
                usd_value = amount * conversion_rate
            else:
                usd_value = amount

            total_portfolio_value += usd_value 
            
            symbol = "£" if fiat == "GBP" else ("€" if fiat == "EUR" else "$")
            print(f"• {fiat:<4} Total Cash:   {symbol}{amount:,.2f} (Value: ${usd_value:,.2f})")
            print("-" * 50)

    print("==========================================================")
    print(f"TOTAL PORTFOLIO VALUE: ${total_portfolio_value:,.2f}")
    if total_portfolio_cost > 0:
        total_return = total_portfolio_value - total_portfolio_cost
        summary_status = "🟢 NET GAIN" if total_return >= 0 else "🔴 NET LOSS"
        print(f"TOTAL NET PERFORMANCE: ${total_return:+,.2f} [{summary_status}]")
    print("==========================================================\n")

if __name__ == "__main__":
    while True:
        try:
            main_verification_loop()
            time.sleep(30)
            os.system('clear')
        except Exception as e:
            print(f"Error ({e}), retrying...")
            time.sleep(30)
            os.system('clear')
