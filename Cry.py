import requests

def fetch_price(ticker):
    url = 'https://api.coingecko.com/api/v3/simple/price?ids=' + ticker + '&vs_currencies=usd'
    response = requests.get(url)
    price_data = response.json()
    return price_data[ticker]['usd']
x = fetch_price(bitcoin)
print(x)
