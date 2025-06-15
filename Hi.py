import requests, time, os, BeautifulSoup 

url = 'https://30rates.com/ethereum-price-prediction-tomorrow-week-month-eth-forecast'
response = requests.get(url)
data = response.json()
print(data)
