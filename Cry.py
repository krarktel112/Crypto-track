import requests

def fetch_price(ticker):
    url = 'https://api.coingecko.com/api/v3/simple/price?ids=' + ticker + '&vs_currencies=usd'
    response = requests.get(url)
    price_data = response.json()
    return price_data[ticker]['usd']
x = fetch_price("bitcoin")
current_value1 = round((x*0.00008288), 2)
profit1 = round(((x*0.00008288)-8), 2)
y = fetch_price("ethereum")
current_value2 = round((y*0.37887184), 2)
current_value3 = round((y*0.001963), 2)
profit2 = (current_value2-1092.2)
profit3 = current_value3
print(f"Bitcoin: {x} | Current value: {current_value1} | Profit: {profit1}")
print(f"Ethereum: {y} | Current value: {current_value2} | Profit: {profit2}")
print(f"Ethereum: {y} | Current value: {current_value3} | Profit: {profit3}")
