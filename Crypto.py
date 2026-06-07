import requests, time, os

portfolio = {
    #'BTC': 0,  # Amount of Bitcoin you own
    'ETH': 0.00000364,  # Amount of Ethereum you own
    'SOL': 0.051808054
    # Add more cryptocurrencies here
}

portfolio2 = {
    #0.04282419 eth
    #0.054997936 sol
    #'BTC': 0.000066,  # Amount of Bitcoin you own
    'ETH': 0.00000364,  # Amount of Ethereum you own
    'SOL': 0.000350292
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
    ethereum = 0
    solo = 4.8
    bitcoin = 0
    for ticker, amount in portfolio.items():
        price = get_crypto_price(ticker)
        value = amount * price
        total_value += value
        #print(f"{ticker}: ${price:.2f} (You own {amount} {ticker}, Value: ${value:.2f})")
        if ticker == "BTC":
            value2 = value - value 
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
def conversion():
    bitcoin = get_crypto_price("BTC")
    ethereum = get_crypto_price("ETH")
    solana = get_crypto_price("SOL")
    recover = (10216.3)
    value = (((recover/ethereum)/0.04307645)*0.15)
    value2 = (((recover/solana)/0.051702936)*0.01)
    x = ethereum/recover
    y = recover/solana
    rounded_num = round(value, 2)
    rounded_num2 = round(value2, 2)
    rounded_num3 = round(x, 5)
    rounded_num4 = round(y, 5)
    print(f"Ethereum {rounded_num3}: ${value:.2f}")
    print(f"Solana {rounded_num4}: ${value2:.2f}")

def conversion2():
    bitcoin = get_crypto_price("BTC")
    ethereum = get_crypto_price("ETH")
    solana = get_crypto_price("SOL")
    recover = (10216.3-6914.02)
    value = (((recover/ethereum)/0.04307645)*0.15)
    value2 = (((recover/solana)/0.051702936)*0.01)
    x = ethereum/recover
    y = recover/solana
    rounded_num = round(value, 2)
    rounded_num2 = round(value2, 2)
    rounded_num3 = round(x, 5)
    rounded_num4 = round(y, 5)
    print(f"Ethereum {rounded_num3}: ${value:.2f}")
    print(f"Solana {rounded_num4}: ${value2:.2f}")

def main():
    while True:
        try:
            display_portfolio(portfolio, portfolio2)
            conversion()
            conversion2()
        except:
            print("Error, retrying.")
        time.sleep(30)
        os.system('clear')

if __name__ == "__main__":
    main()
