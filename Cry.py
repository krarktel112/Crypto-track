import requests
#import winsound

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

def display_portfolio(portfolio, rewards):
    print(f"----------------------------------------------------------\n")
    total_value = 0.0
    for ticker, amount in portfolio.items():
        price = fetch_price(ticker)
        price1 = round(price, 2)
        value = amount * price
        total_value += float(value)
        value1 = round(value, 2)
        #total_value1 = round(total_value, 2)
        print(f"{ticker}: ${price1} (You own {amount} {ticker}, Value: ${value1})")
    #print(f"Total Portfolio Value: ${total_value1}\n")
    for ticker, amount in rewards.items():
        price = fetch_price(ticker)
        price1 = round(price, 2)
        value = amount * price
        total_value += float(value)
        value1 = round(value, 2)
        #total_value1 = round(total_value, 2)
        print(f"{ticker}: ${price1} (You own {amount} {ticker}, Value: ${value1})")
    #print(f"Total Portfolio Value: ${total_value:.2f}\n")

#y = fetch_price("ethereum")
#if y>= 2882.2:
#    winsound.PlaySound('path/to/your/audiofile.wav', winsound.SND_FILENAME)
#else:
#    zed == 0
port = process_text_file_to_dict(file_path)
rew = process_text_file_to_dict(file_path2)
#print(port)
#print(rew)
display_portfolio(port, rew)
