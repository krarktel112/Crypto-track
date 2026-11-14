import os
from coinbase.rest import RESTClient

API_KEY_NAME = os.environ.get("COINBASE_API_KEY_NAME")
API_SECRET_KEY = os.environ.get("COINBASE_API_SECRET")
client = RESTClient(api_key=API_KEY_NAME, api_secret=API_SECRET_KEY)

def evaluate_market_logic():
    """
    Evaluates live market conditions and executes trades automatically 
    when thresholds are met on the TrueNAS backend.
    """
    print("⚙️ Market Engine: Evaluating live conditions...")

    try:
        # Example: Fetch live BTC price
        product = client.get_product(product_id="BTC-USD")
        spot_price = float(product.price) if hasattr(product, "price") else float(product.get("price", 0))

        # --- DEFINE YOUR THRESHOLD CONDITIONS HERE ---
        # Example condition: If BTC drops below a target dip price, execute a buy order
        TARGET_BUY_THRESHOLD = 60000.00  # Change to your target dip price
        
        if spot_price > 0 and spot_price <= TARGET_BUY_THRESHOLD:
            print(f"🚨 TARGET HIT! BTC is at ${spot_price:,.2f} (<= ${TARGET_BUY_THRESHOLD:,.2f})")
            
            # --- LIVE ORDER EXECUTION ---
            # Uncomment below to enable live order placement via Coinbase API:
            # order = client.create_order(
            #     product_id="BTC-USD",
            #     side="BUY",
            #     order_configuration={"market_market_ioc": {"quote_size": "10.00"}} # Buy $10 of BTC
            # )
            # print(f"✅ Trade Executed Successfully: {order}")
        else:
            print(f"📊 Market stable. BTC Spot: ${spot_price:,.2f} (Target: ${TARGET_BUY_THRESHOLD:,.2f})")

    except Exception as e:
        print(f"⚠️ Market Engine Execution Error: {e}")
