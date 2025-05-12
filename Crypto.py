import requests, time, os

portfolio = {
    'BTC': 0.00008288,  # Amount of Bitcoin you own
    'ETH': 0.37895131,  # Amount of Ethereum you own
    # Add more cryptocurrencies here
}

portfolio2 = {
    #'BTC': 0,  # Amount of Bitcoin you own
    'ETH': 0.002043,  # Amount of Ethereum you own
    # Add more cryptocurrencies here
}
# Note some tokens aren't available on Coinbase
def process_text_file_to_dict(file_path):
    data_dict = {}
    try:
        with open(file_path, 'r') as file:
            for line in file:
                key, value = line.strip().split(': ')  # Assuming key: value format
                data_dict[key] = value
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None
    except ValueError:
         print(f"Error: Invalid format in line: {line.strip()}")
         return None
    return data_dict
file_path = 'Portfolio.txt'
file_path2 = 'Rewards.txt'
portfolio = process_text_file_to_dict(file_path)
rewards = process_text_file_to_dict(file_path2)
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
    print(total_value-1092.2)
    total_value = 0.0
    for ticker, amount in rewards.items():
        price = get_crypto_price(ticker)
        value = amount * price
        total_value += value
        print(f"{ticker}: ${price:.2f} (You own {amount} {ticker}, Value: ${value:.2f})")
    print(f"Total Reward Value: ${total_value:.2f}\n")

def main():
    while True:
        display_portfolio(portfolio, rewards)
        time.sleep(30)
        os.system('clear')

if __name__ == "__main__":
    main()
