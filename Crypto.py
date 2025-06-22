import requests, time, os

portfolio = {
    'BTC': 0.0000181,  # Amount of Bitcoin you own
    'ETH': 0.00000001,  # Amount of Ethereum you own
    'SOL': 0.001035166
    # Add more cryptocurrencies here
}

portfolio2 = {
    'BTC': 0,  # Amount of Bitcoin you own
    'ETH': 0.0,  # Amount of Ethereum you own
    'SOL': 0.0
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
    Ethereum = 0
    solo = 0
    bitcoin = 1.8
    for ticker, amount in portfolio.items():
        price = get_crypto_price(ticker)
        value = amount * price
        
        value3 = value - Ethereum 
        value4 = value - solo
        total_value += value
        #print(f"{ticker}: ${price:.2f} (You own {amount} {ticker}, Value: ${value:.2f})")
        if ticker == "BTC":
            value2 = value - bitcoin
            print(f"{ticker}: ${price:.2f} (You own {amount} {ticker}, Value: ${value:.2f}, Profit: ${value2:.2f})")
        elif ticker == "ETH":
            value2 = value - Ethereum 
            print(f"{ticker}: ${price:.2f} (You own {amount} {ticker}, Value: ${value:.2f}, Profit: ${value2:.2f})")
        elif ticker == "SOL":
            value2 = value - solo
            print(f"{ticker}: ${price:.2f} (You own {amount} {ticker}, Value: ${value:.2f}, Profit: ${value2:.2f})")
    print(f"Total Portfolio Value: ${total_value:.2f}\n")
    ding = get_crypto_price("ETH")
    if ding <= 2878.44:
        ding == 0
    else:
        zoink = "/data/data/com.termux/files/home/termux-melody-every-1-minut/melody1.mp3"
        os.system("play-audio " + zoink)

def main():
    while True:
        try:
            display_portfolio(portfolio)
        except:
            print("Error, retrying.")
        time.sleep(30)
        os.system('clear')

if __name__ == "__main__":
    main()
