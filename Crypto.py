import requests, time, os

value1 = input("Total here:") or int(0)
value2 = input("Bonus here:") or int(0)
portfolio = {
    #'BTC': 0,  # Amount of Bitcoin you own
    'ETH': (value1),  # Amount of Ethereum you own
    # Add more cryptocurrencies here
}

portfolio2 = {
    #'BTC': 0,  # Amount of Bitcoin you own
    'ETH': (value2),  # Amount of Ethereum you own
    # Add more cryptocurrencies here
}
# Note some tokens aren't available on Coinbase
def get_crypto_price(ticker):
    url = f'https://api.coinbase.com/v2/prices/{ticker}-USD/spot'
    response = requests.get(url)
    data = response.json()
    return float(data['data']['amount'])

def display_portfolio(portfolio):
    print(f"----------------------------------------------------------\n")
    total_value = 0.0
    for ticker, amount in portfolio.items():
        price = get_crypto_price(ticker)
        value = amount * price
        total_value += value
        print(f"{ticker}: ${price:.2f} (You own {amount} {ticker}, Value: ${value:.2f})")
    print(f"Total Portfolio Value: ${total_value:.2f}\n")

def pause_and_adjust(value):
    """Pauses the script, allows user to adjust a value, and returns the updated value."""
    print(f"Current value: {value}")
    try:
        new_value = input("Enter a new value (or press Enter to keep the current value): ")
        if new_value:
            value = type(value)(new_value)  # Attempt to cast to the original type
    except ValueError:
         print("Invalid input. Keeping the current value.")
    input("Press Enter to continue...")
    return value

def main():
    while True:
        display_portfolio(portfolio)
        display_portfolio(portfolio2)
        time.sleep(30)
        os.system('clear')

if __name__ == "__main__":
    main()
