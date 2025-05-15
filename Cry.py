import requests
#import winsound

def process_file_and_loop(file_path):
    """
    Reads a text file, creates a dictionary, and iterates through it using .items().

    Args:
        file_path (str): The path to the text file.
    """

    data_dict = {}
    try:
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()  # Remove leading/trailing whitespace
                if line:  # Skip empty lines
                    key, value = line.split(':', 1)  # Split into key and value
                    data_dict[key.strip()] = value.strip()
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return

    for key, value in data_dict.items():
        print(f"Key: {key}, Value: {value}")
    return data_dict

# Example usage:
file_path = 'Portfolio.txt'  # Replace with your file path
file_path2 = 'Rewards.txt'
# Create a dummy data.txt file for testing

def fetch_price(ticker):
    url = 'https://api.coingecko.com/api/v3/simple/price?ids=' + ticker + '&vs_currencies=usd'
    response = requests.get(url)
    price_data = response.json()
    return price_data[ticker]['usd']

def display_portfolio():
    print(f"----------------------------------------------------------\n")
    total_value = 0.0
    file_path = 'Portfolio.txt'  # Replace with your file path
    file_path2 = 'Rewards.txt'
    portfolio = process_file_and_loop(file_path)
    for ticker, amount in portfolio.items():
        price = int(fetch_price(ticker))
        price1 = round(price, 2)
        value = amount * int(price)
        total_value += value
        value1 = round(value, 2)
        #total_value1 = round(total_value, 2)
        print(f"{ticker}: ${price1} (You own {amount} {ticker}, Value: ${value1})")
    print(f"Total Portfolio Value: ${total_value1}\n")
    total_value = 0.0
    rewards = process_file_and_loop(file_path2)
    for ticker, amount in rewards.items():
        price = fetch_price(ticker)
        price1 = round(price, 2)
        value = amount * price
        total_value += int(value)
        value1 = round(value, 2)
        total_value1 = round(total_value, 2)
        print(f"{ticker}: ${price1} (You own {amount} {ticker}, Value: ${value1})")
    print(f"Total Portfolio Value: ${total_value:.2f}\n")

#y = fetch_price("ethereum")
#if y>= 2882.2:
#    winsound.PlaySound('path/to/your/audiofile.wav', winsound.SND_FILENAME)
#else:
#    zed == 0
port = process_file_and_loop(file_path)
rew = process_file_and_loop(file_path2)
print(port)
print(rew)
display_portfolio()
