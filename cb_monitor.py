import os
import time
import json
import re
import imaplib
import email
import banking_engine
import grid_engine
import cost_basis
import market_engine
from email.header import decode_header
from coinbase.rest import RESTClient

# --- SECURE CREDENTIAL ARRAYS ---
API_KEY_NAME = os.environ.get("COINBASE_API_KEY_NAME", "your_api_key_name_here")
API_SECRET_KEY = os.environ.get("COINBASE_API_SECRET", "your_api_secret_key_here")

YAHOO_USER = os.environ.get("YAHOO_EMAIL_ADDRESS", "your_email@yahoo.com")
YAHOO_PASS = os.environ.get("YAHOO_APP_PASSWORD", "your_yahoo_app_password")

client = RESTClient(api_key=API_KEY_NAME, api_secret=API_SECRET_KEY)
STATE_FILE = "portfolio_state.json"

# Tokens listed here will NEVER be overwritten by live API balances (managed manually via JSON)
MANUALLY_MANAGED_TOKENS = {"SOL", "ATOM"}

def load_local_portfolio_state():
    """Reads the last cached balance sheet structure from local storage."""
    defaults = {
        "SOL": {"balance": 0.118511109, "avg_buy": 0.01},
        "ATOM": {"balance": 4.742292, "avg_buy": 0.01},
        "BTC": {"balance": 0.00000000, "avg_buy": 0.01},
        "ETH": {"balance": 0.00000009, "avg_buy": 0.01}
    }
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                data = json.load(f)
                
                if "assets" in data:
                    flat_data = {}
                    for token, details in data["assets"].items():
                        flat_data[token] = {
                            "balance": details.get("balance", 0.0),
                            "avg_buy": details.get("avg_buy", 0.0)
                        }
                    return flat_data
                
                crypto_assets = {}
                for key, val in data.items():
                    if isinstance(val, dict) and "balance" in val:
                        crypto_assets[key] = val
                return crypto_assets if crypto_assets else defaults
        except:
            pass
    return defaults

def save_local_portfolio_state(state):
    """Saves active balance changes locally while preserving non-asset metadata."""
    try:
        existing_data = {}
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r") as f:
                    existing_data = json.load(f)
            except:
                pass

        existing_data.update(state)

        with open(STATE_FILE, "w") as f:
            json.dump(existing_data, f, indent=4)
    except:
        pass

def scrape_yahoo_transaction_updates(state):
    """Logs into your Yahoo profile via secure IMAP to scan and pull recent balance modifications."""
    if not YAHOO_PASS or "your_yahoo" in YAHOO_PASS:
        return state

    try:
        mail = imaplib.IMAP4_SSL("imap.mail.yahoo.com", 993)
        mail.login(YAHOO_USER, YAHOO_PASS)
        mail.select("Inbox")

        status, messages = mail.search(None, '(FROM "no-reply@coinbase.com")')
        if status != "OK":
            return state

        email_ids = messages[0].split()
        for e_id in email_ids[-15:]:
            res, msg_data = mail.fetch(e_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding or "utf-8")
                    
                    subject = subject.upper()

                    if "SOLD" in subject:
                        match = re.search(r"(?:YOU\s+)?SOLD\s+(?:\$?[\d\.]+\s+OF\s+|[\d\.]+\s+)?([A-Z0-9]+)", subject)
                        if match:
                            ticker = match.group(1)
                            if ticker in state and ticker not in MANUALLY_MANAGED_TOKENS:
                                state[ticker]["balance"] = 0.00000000
        mail.logout()
    except Exception:
        pass
    return state

def get_live_price(ticker):
    """Fetches real-time spot market pricing directly from Coinbase CDP SDK."""
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
    """Aggregates balances honoring JSON configurations for staked assets while live-tracking BTC."""
    portfolio_state = load_local_portfolio_state()
    
    portfolio_state = scrape_yahoo_transaction_updates(portfolio_state)
    save_local_portfolio_state(portfolio_state)

    try:
        response = client.get_accounts(limit=250)
        data = response.to_dict() if hasattr(response, "to_dict") else (response if isinstance(response, dict) else {})
        accounts = data.get("accounts", [])
    except Exception as e:
        print(f"❌ API Failure: {e}")
        return

    print("\n==========================================================")
    print("             VERIFIED REAL-TIME TOTAL BALANCES            ")
    print("==========================================================")

    total_portfolio_value = 0.0
    total_portfolio_cost = 0.0
    cash_balances = {"USD": 0.0, "EUR": 0.0, "GBP": 0.0}

    for acc in accounts:
        currency_ticker = str(acc.get("currency", "")).upper().strip()
        if currency_ticker in cash_balances:
            try:
                available = float(acc.get("available_balance", {}).get("value", "0"))
                held = float(acc.get("hold", {}).get("value", "0"))
                cash_balances[currency_ticker] += (available + held)
            except:
                pass

    for token in sorted(portfolio_state.keys()):
        liquid_balance = 0.0
        for acc in accounts:
            if str(acc.get("currency", "")).upper().strip() == token:
                try:
                    available = float(acc.get("available_balance", {}).get("value", "0"))
                    held = float(acc.get("hold", {}).get("value", "0"))
                    liquid_balance += (available + held)
                except:
                    pass
        
        stored_balance = portfolio_state[token]["balance"]
        
        # --- HYBRID LOGIC ---
        if token in MANUALLY_MANAGED_TOKENS:
            total_balance = stored_balance
        else:
            if liquid_balance == 0.0 and stored_balance > 0.0:
                portfolio_state[token]["balance"] = 0.0
                total_balance = 0.0
                save_local_portfolio_state(portfolio_state)
            elif liquid_balance > 0.0 and liquid_balance != stored_balance:
                portfolio_state[token]["balance"] = liquid_balance
                total_balance = liquid_balance
                save_local_portfolio_state(portfolio_state)
            else:
                total_balance = stored_balance

        avg_buy = portfolio_state[token]["avg_buy"]

        live_spot_price = get_live_price(token)
        current_value = total_balance * live_spot_price
        initial_cost = total_balance * avg_buy
        net_profit = current_value - initial_cost
        
        total_portfolio_value += current_value
        total_portfolio_cost += initial_cost

        print(f"• {token:<4} Total Amount: {total_balance:.8f}")
        print(f"       Avg Buy Price: ${avg_buy:,.2f} | Live Spot: ${live_spot_price:,.2f}")
        
        # --- SATOSHI CALCULATION ---
        if token == "BTC" and live_spot_price > 0:
            sats_per_dollar = 100_000_000 / live_spot_price
            print(f"       Sats per USD:  {sats_per_dollar:,.0f} sats/$1")

        print(f"       Holding Value: ${current_value:,.2f}")
        
        if avg_buy > 0:
            status = "🟢 PROFIT" if net_profit >= 0 else "🔴 LOSS"
            print(f"       Net Return:    ${net_profit:+,.2f} [{status}]")
        print("-" * 50)

    has_cash = False
    for fiat, amount in cash_balances.items():
        if amount > 0:
            if not has_cash:
                print("                     FIAT CASH BALANCES                   ")
                print("-" * 50)
                has_cash = True
            usd_value = amount if fiat == "USD" else (amount * get_live_price(fiat))
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

    # --- EXECUTE SUB-MODULES ---
    try:
        banking_engine.process_banking_logic()
    except Exception as e:
        print(f"⚠️ Banking Engine Error: {e}\n")

    try:
        grid_engine.initialize_grid()
    except Exception as e:
        print(f"⚠️ Grid Engine Error: {e}\n")

    try:
        cost_basis.calculate_true_averages()
    except Exception as e:
        print(f"⚠️ Cost Basis Engine Error: {e}\n")

    try:
        market_engine.evaluate_market_logic()
    except Exception as e:
        print(f"⚠️ Market Engine Error: {e}\n")

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
