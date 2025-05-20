import requests, time, os

portfolio = {
    #'BTC': 0.0,  # Amount of Bitcoin you own
    'ETH': 0.37906705,  # Amount of Ethereum you own
    # Add more cryptocurrencies here
}

portfolio2 = {
    #'BTC': 0,  # Amount of Bitcoin you own
    'ETH': 0.002159,  # Amount of Ethereum you own
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
    for ticker, amount in portfolio.items():
        price = get_crypto_price(ticker)
        value = amount * price
        total_value += value
        print(f"{ticker}: ${price:.2f} (You own {amount} {ticker}, Value: ${value:.2f})")
    print(f"Total Portfolio Value: ${total_value:.2f}\n")
    zed = total_value - 1092.2
    total_value = 0.0
    for ticker, amount in rewards.items():
        price = get_crypto_price(ticker)
        value = amount * price
        total_value += value
        print(f"{ticker}: ${price:.2f} (You own {amount} {ticker}, Value: ${value:.2f})")
    print(f"Total Reward Value: ${total_value:.2f}\n")
    formatted_number = f"{zed:.2f}"
    print(formatted_number)
    ding = get_crypto_price("ETH")
    if ding <= 2882.2:
        ding == 0
    else:
        zoink = "/data/data/com.termux/files/home/termux-melody-every-1-minut/melody1.mp3"
        os.system("play-audio " + zoink)

def main():
    while True:
        display_portfolio(portfolio, portfolio2)
        time.sleep(30)
        os.system('clear')

if __name__ == "__main__":
    main()
