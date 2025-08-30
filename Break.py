import requests, time, os

def sell(x):
    if x < 10:
        y = 0.03
    elif x <= 100:
        y = 0.0225
    elif x <= 200:
       y = 0.02
    elif x <= 1000:
        y = 0.0175
    elif x <= 2000:
        y = 0.015
    elif x <= 3000:
        y = 0.0125
    elif x <= 5000:
        y = 0.01
    elif x > 5000:
        y = 0.0075
    else:
        quit()
    return y

def get_crypto_price(ticker):
    url = f'https://api.coinbase.com/v2/prices/{ticker}-USD/spot'
    response = requests.get(url)
    data = response.json()
    return float(data['data']['amount'])

def calculate_bitcoin_break_even(initial_investment, buy_fee_percentage, sell_fee_percentage, bitcoin_price_at_purchase):
    """
    Calculates the break-even price for a Bitcoin trade, including buy and sell fees.

    Args:
        initial_investment (float): The total amount invested (e.g., $1000).
        buy_fee_percentage (float): The exchange fee percentage for buying (e.g., 0.001 for 0.1%).
        sell_fee_percentage (float): The exchange fee percentage for selling (e.g., 0.001 for 0.1%).
        bitcoin_price_at_purchase (float): The price of Bitcoin at the time of purchase.

    Returns:
        float: The break-even price per Bitcoin.
    """

    # Calculate the amount of Bitcoin purchased
    bitcoin_purchased = (int(initial_investment) * (1 - buy_fee_percentage)) / int(bitcoin_price_at_purchase)  # Note: assuming buy_fee is applied to the fiat amount

    # Calculate the total cost including fees for the trade
    total_cost = int(initial_investment) + (int(initial_investment) * buy_fee_percentage) 

    # Calculate the break-even selling price (accounting for the sell fee as a percentage of the selling price)
    break_even_price = total_cost / (bitcoin_purchased * (1 - sell_fee_percentage))

    return break_even_price

# Example Usage:
initial_investment = input("Investment:") # $1000 USD
buy_fee_percentage = sell(initial_investment) # 0.1% buy fee
sell_fee_percentage = sell(initial_investment) # 0.1% sell fee
bitcoin_price_at_purchase = get_crypto_price("BTC") # Bitcoin price at time of purchase

break_even = calculate_bitcoin_break_even(initial_investment, buy_fee_percentage, sell_fee_percentage, bitcoin_price_at_purchase)

print(f"The break-even price for your Bitcoin trade is: ${break_even:.2f}") 
