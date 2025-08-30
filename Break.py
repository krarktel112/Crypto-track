import requests, time, os



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
buy_fee_percentage = 0.02  # 0.1% buy fee
sell_fee_percentage = 0.02  # 0.1% sell fee
bitcoin_price_at_purchase = input("Price:") # Bitcoin price at time of purchase

break_even = calculate_bitcoin_break_even(initial_investment, buy_fee_percentage, sell_fee_percentage, bitcoin_price_at_purchase)
break_even1 = calculate_bitcoin_break_even(initial_investment, 0.03, 0.03, bitcoin_price_at_purchase)
break_even2 = calculate_bitcoin_break_even(initial_investment, 0.0225, 0.0225, bitcoin_price_at_purchase)
break_even3 = calculate_bitcoin_break_even(initial_investment, 0.02, 0.02, bitcoin_price_at_purchase)
break_even4 = calculate_bitcoin_break_even(initial_investment, 0.0175, 0.0175, bitcoin_price_at_purchase)
break_even5 = calculate_bitcoin_break_even(initial_investment, 0.015, 0.015, bitcoin_price_at_purchase)
break_even6 = calculate_bitcoin_break_even(initial_investment, 0.0125, 0.0125, bitcoin_price_at_purchase)
break_even7 = calculate_bitcoin_break_even(initial_investment, 0.01, 0.01, bitcoin_price_at_purchase)
break_even8 = calculate_bitcoin_break_even(initial_investment, 0.0075, 0.0075, bitcoin_price_at_purchase)

print(f"The break-even price for your Bitcoin trade is: ${break_even:.2f}") 
print(f"The break-even price for your Bitcoin trade is: ${break_even1:.2f}") 
print(f"The break-even price for your Bitcoin trade is: ${break_even2:.2f}") 
print(f"The break-even price for your Bitcoin trade is: ${break_even3:.2f}") 
print(f"The break-even price for your Bitcoin trade is: ${break_even4:.2f}") 
print(f"The break-even price for your Bitcoin trade is: ${break_even5:.2f}") 
print(f"The break-even price for your Bitcoin trade is: ${break_even6:.2f}") 
print(f"The break-even price for your Bitcoin trade is: ${break_even7:.2f}") 
print(f"The break-even price for your Bitcoin trade is: ${break_even8:.2f}") 

print(get_crypto_price("BTC"))
