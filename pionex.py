import time
import uuid
from coinbase.rest import RESTClient

# --- CONFIGURATION ---
API_KEY = "organizations/YOUR_ORG_ID/apiKeys/YOUR_KEY_ID"
API_SECRET = "-----BEGIN EC PRIVATE KEY-----\nYOUR_SECRET_KEY\n-----END EC PRIVATE KEY-----"

PRODUCT_ID = "BTC-USD"
DCA_AMOUNT_USD = "2.00"      # ABSOLUTE MINIMUM FOR A 2-TRANCHE SPLIT
NUMBER_OF_SELL_TRANCHES = 2   # Kept at 2 so each sell order is ~$1.00

MIN_PROFIT_PCT = 0.02         # 2% minimum profit for quick testing
MAX_PROFIT_PCT = 0.05         # 5% maximum profit
# ---------------------

client = RESTClient(api_key_string=API_KEY, signature_secret_string=API_SECRET)

def execute_micro_dca():
    print(f"🤖 Initializing test on {PRODUCT_ID}...")
    
    # 1. Market Buy
    try:
        buy_order = client.create_order(
            client_order_id=str(uuid.uuid4()),
            product_id=PRODUCT_ID,
            side="BUY",
            order_configuration={"market_market_ioc": {"quote_size": DCA_AMOUNT_USD}}
        )
        print("✅ DCA Buy Order Submitted.")
    except Exception as e:
        print(f"❌ Buy Failed (Check if account has USD balance): {e}")
        return

    time.sleep(3) # Wait for order engine to settle
    
    # 2. Get Order Details
    try:
        order_details = client.get_order(order_id=buy_order['order_id'])
        avg_fill_price = float(order_details['order']['avg_price'])
        amount_filled_crypto = float(order_details['order']['filled_size'])
        print(f"📊 Filled: {amount_filled_crypto} BTC at ${avg_fill_price:.2f}")
    except Exception as e:
        print(f"❌ Failed to fetch buy details: {e}")
        return

    # 3. Math & Tranche Placement
    crypto_per_sell_order = amount_filled_crypto / NUMBER_OF_SELL_TRANCHES
    
    price_steps = []
    step_size = (MAX_PROFIT_PCT - MIN_PROFIT_PCT) / (NUMBER_OF_SELL_TRANCHES - 1)
    for i in range(NUMBER_OF_SELL_TRANCHES):
        target_pct = MIN_PROFIT_PCT + (step_size * i)
        price_steps.append(avg_fill_price * (1 + target_pct))

    # 4. Place Limit Sells
    for idx, target_price in enumerate(price_steps):
        formatted_price = f"{target_price:.2f}"
        # BTC requires up to 8 decimal places for size precision
        formatted_size = f"{crypto_per_sell_order:.8f}" 
        
        try:
            sell_order = client.create_order(
                client_order_id=str(uuid.uuid4()),
                product_id=PRODUCT_ID,
                side="SELL",
                order_configuration={
                    "limit_limit_gtc": {
                        "base_size": formatted_size,
                        "limit_price": formatted_price,
                        "post_only": False # False for testing to ensure order accepts smoothly
                    }
                }
            )
            print(f" ➡️ Sell Tranche {idx+1}: {formatted_size} BTC at ${formatted_price}")
        except Exception as e:
            print(f" ⚠️ Tranche {idx+1} Rejected: {e} (Likely size fell below $1.00 minimum)")

if __name__ == "__main__":
    execute_micro_dca()
