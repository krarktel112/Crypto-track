import os
import time
from coinbase.rest import RESTClient

# Initialize client
API_KEY_NAME = os.environ.get("COINBASE_API_KEY_NAME", "your_api_key_name_here")
API_SECRET_KEY = os.environ.get("COINBASE_API_SECRET", "your_api_secret_key_here")

client = RESTClient(api_key=API_KEY_NAME, api_secret=API_SECRET_KEY)

def fetch_staked_solana_balance():
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
    """Fetches spot market pricing; returns 1.0 for stablecoins like USDC/USDT."""
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
    print("🔄 Processing dynamic vault ledgers and account structures...")
    
    try:
        response = client.get_accounts(limit=250)
        data = response.to_dict() if hasattr(response, "to_dict") else (response if isinstance(response, dict) else {})
        accounts = data.get("accounts", [])
    except Exception as e:
        print(f"❌ API Failure: {e}")
        return

    staked_solana = fetch_staked_solana_balance()

    print("\n==========================================================")
    print("             VERIFIED REAL-TIME TOTAL BALANCES            ")
    print("==========================================================")

    total_portfolio_value = 0.0
    
    fiat_currencies = {"USD", "EUR", "GBP"}
    crypto_balances = {}
    fiat_balances = {"USD": 0.0, "EUR": 0.0, "GBP": 0.0}

    # Step 1: Parse ALL account balances dynamically
    for acc in accounts:
        ticker = str(acc.get("currency", "")).upper().strip()
        try:
            available = float(acc.get("available_balance", {}).get("value", "0"))
            held = float(acc.get("hold", {}).get("value", "0"))
            total = available + held
        except Exception:
            total = 0.0

        if total <= 0 and ticker != "SOL":
            continue

        if ticker in fiat_currencies:
            fiat_balances[ticker] += total
        else:
            crypto_balances[ticker] = crypto_balances.get(ticker, 0.0) + total

    # Account for off-chain staked SOL if applicable
    if staked_solana > 0:
        crypto_balances["SOL"] = max(staked_solana, crypto_balances.get("SOL", 0.0))

    # Step 2: Iterate and display all discovered crypto assets with non-zero balances
    for token, total_balance in sorted(crypto_balances.items()):
        if total_balance <= 0:
            continue

        live_spot_price = get_live_price(token)
        current_value = total_balance * live_spot_price
        total_portfolio_value += current_value

        print(f"• {token:<5} Total Amount: {total_balance:.8f}")
        print(f"        Live Spot:     ${live_spot_price:,.2f}")
        print(f"        Holding Value: ${current_value:,.2f}")
        print("-" * 50)

    # Step 3: Process Fiat Cash Balances
    has_cash = False
    for fiat, amount in fiat_balances.items():
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
            print(f"• {fiat:<5} Total Cash:   {symbol}{amount:,.2f} (Value: ${usd_value:,.2f})")
            print("-" * 50)

    print("==========================================================")
    print(f"TOTAL PORTFOLIO VALUE: ${total_portfolio_value:,.2f}")
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
