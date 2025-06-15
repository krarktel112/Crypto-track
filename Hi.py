import requests, time, os
from bs4 import BeautifulSoup

url = 'https://30rates.com/ethereum-price-prediction-tomorrow-week-month-eth-forecast'
response = requests.get(url)
html_content = response.text
#soup = 

print(html_content)
