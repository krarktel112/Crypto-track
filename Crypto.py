import requests, time, os

portfolio = {
    #'BTC': 0,  # Amount of Bitcoin you own
    'ETH': 0.04283023,  # Amount of Ethereum you own
    'SOL': 0.05510602
    # Add more cryptocurrencies here
}

portfolio2 = {
    #0.04282419 eth
    #0.054997936 sol
    #'BTC': 0.000066,  # Amount of Bitcoin you own
    'ETH': 0.00022054,  # Amount of Ethereum you own
    'SOL': 0.000108084
    # Add more cryptocurrencies here
}
# Note some tokens aren't available on Coinbase

def get_crypto_price(ticker):
    url = f'https://api.coinbase.com/v2/prices/{ticker}-USD/spot'
    response = requests.get(url)
    data = response.json()
    return float(data['data']['amount'])

def display_portfolio(portfolio, rewards):
    print(f"----------------------------------------------------------\n")
    total_value = 0.0
    total_profit = 0.0
    ethereum = 99.22
    solo = 4.8
    bitcoin = 0
    for ticker, amount in portfolio.items():
        price = get_crypto_price(ticker)
        value = amount * price
        total_value += value
        #print(f"{ticker}: ${price:.2f} (You own {amount} {ticker}, Value: ${value:.2f})")
        if ticker == "BTC":
            value2 = value - bitcoin - (value * 0.02)
            print(f"{ticker}: ${price:.2f} (You own {amount} {ticker}, Value: ${value:.2f}, Profit: ${value2:.2f})")
            total_profit += value2
        elif ticker == "ETH":
            value2 = value - ethereum - (value * 0.02)
            print(f"{ticker}: ${price:.2f} (You own {amount} {ticker}, Value: ${value:.2f}, Profit: ${value2:.2f})")
            total_profit += value2
        elif ticker == "SOL":
            value2 = value - solo - (value * 0.02)
            print(f"{ticker}: ${price:.2f} (You own {amount} {ticker}, Value: ${value:.2f}, Profit: ${value2:.2f})")
            total_profit += value2
    print(f"Total Portfolio Value: ${total_value:.2f} Total profit: ${total_profit:.2f}\n")
    total_value = 0.0
    total_profit = 0.0
    for ticker, amount in rewards.items():
        price = get_crypto_price(ticker)
        value = amount * price
        total_value += value
        print(f"{ticker}: ${price:.2f} (You own {amount} {ticker}, Value: ${value:.2f})")
    print(f"Total Reward Value: ${total_value:.2f}\n")

def main():
    while True:
        try:
            display_portfolio(portfolio, portfolio2)
        except:
            print("Error, retrying.")
        time.sleep(30)
        os.system('clear')

if __name__ == "__main__":
    main()
