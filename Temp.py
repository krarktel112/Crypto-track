initial_investment = input("Investment:") # $1000 USD
buy_fee_percentage = 0.02  # 0.1% buy fee
sell_fee_percentage = 0.02  # 0.1% sell fee
bitcoin_price_at_purchase = input("Price:") # Bitcoin price at time of purchase


    # Calculate the amount of Bitcoin purchased
bitcoin_purchased = (initial_investment * (1 - buy_fee_percentage)) / bitcoin_price_at_purchase
total_cost = initial_investment + (initial_investment * buy_fee_percentage) 

    # Calculate the break-even selling price (accounting for the sell fee as a percentage of the selling price)
break_even_price = total_cost / (bitcoin_purchased * (1 - sell_fee_percentage))


# Example Usage:

break_even = break_even_price

print(f"The break-even price for your Bitcoin trade is: ${break_even:.2f}") 
