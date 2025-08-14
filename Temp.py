initial_investment = input("Investment:") # $1000 USD
buy_fee_percentage = 0.02  # 0.1% buy fee
sell_fee_percentage = 0.02  # 0.1% sell fee
bitcoin_price_at_purchase = input("Price:") # Bitcoin price at time of purchase


    # Calculate the amount of Bitcoin purchased
bitcoin_purchased = (int(initial_investment) * 0.98) / int(bitcoin_price_at_purchase)
total_cost = initial_investment + (initial_investment * 0.02) 

    # Calculate the break-even selling price (accounting for the sell fee as a percentage of the selling price)
break_even_price = total_cost / (bitcoin_purchased * (0.98))


# Example Usage:

break_even = break_even_price

print(f"The break-even price for your Bitcoin trade is: ${break_even:.2f}") 
