import requests

portfolio = {
    bitcoin:0.00008288
    ethereum:0.37887184
}
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
def fetch_price(ticker):
    url = 'https://api.coingecko.com/api/v3/simple/price?ids=' + ticker + '&vs_currencies=usd'
    response = requests.get(url)
    price_data = response.json()
    return price_data[ticker]['usd']
def display_portfolio(portfolio):
    print(f"----------------------------------------------------------\n")
    total_value = 0.0
    def display_portfolio(portfolio):
    print(f"----------------------------------------------------------\n")
    total_value = 0.0
    for ticker, amount in portfolio.items():
        price = get_crypto_price(ticker)
        value = amount * price
        total_value += value
        print(f"{ticker}: ${price:.2f} (You own {amount} {ticker}, Value: ${value:.2f})")
    print(f"Total Portfolio Value: ${total_value:.2f}\n")"Total Portfolio Value: ${total_value:.2f}\n")
    for ticker, amount in rewards.items():
        price = get_crypto_price(ticker)
        value = amount * price
        total_value += value
        print(f"{ticker}: ${price:.2f} (You own {amount} {ticker}, Value: ${value:.2f})")
    print(f"Total Portfolio Value: ${total_value:.2f}\n")
x = fetch_price("bitcoin")
current_value1 = round((x*0.00008288), 2)
profit1 = round(((x*0.00008288)-8), 2)
y = fetch_price("ethereum")
current_value2 = round((y*0.37887184), 2)
current_value3 = round((y*0.001963), 2)
profit2 = round(((y*0.37887184)-1092.2), 2)
profit3 = current_value3
print(f"Bitcoin: {x} | Current value: {current_value1} | Profit: {profit1}")
print(f"Ethereum: {y} | Current value: {current_value2} | Profit: {profit2}")
print(f"Ethereum: {y} | Current value: {current_value3} | Profit: {profit3}")
