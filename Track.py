import requests

# Define your API configuration
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjcmVhdGVkQXQiOjE3ODM2NTcyOTUzNDksImVtYWlsIjoia3Jhcmt0ZWxAZ21haWwuY29tIiwiYWN0aW9uIjoidG9rZW4tYXBpIiwiYXBpVmVyc2lvbiI6InYyIiwiaWF0IjoxNzgzNjU3Mjk1fQ.KiDbeb6q8XeS6kUhYfQxg3hCoEvRluDnIE7CA24rwTA"
BASE_URL = "https://solscan.io"

# Set authentication headers
headers = {
    "token": API_KEY,
    "accept": "application/json"
}

def get_account_balance(account_address):
    """Fetches details and token portfolio of a specific Solana account."""
    url = f"{BASE_URL}/account/portfolio"
    params = {"account": account_address}
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        return f"Error: {response.status_code} - {response.text}"

# Example Usage (Replace with a valid public address)
wallet_address = "2d1Yx1tVorsVhZG2ygdi2rJTaa4KMYv112PNoc9TU36c"
data = get_account_balance(wallet_address)
print(data)
