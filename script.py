import requests

baseUrl = "http://10.10.0.2:8085/key-value-store-view"
response = requests.get(baseUrl)

print(response)
