import requests

with open('event.json', 'rt', encoding='utf-8') as f_in:
    event = f_in.read()


url = 'http://localhost:8080/2015-03-31/functions/function/invocations'
response = requests.post(url, json=event, timeout=60)
print(response.json())
