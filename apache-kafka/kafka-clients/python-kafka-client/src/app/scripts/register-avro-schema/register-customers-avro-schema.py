import json
import requests

def pretty(text):
    print(json.dumps(text, indent=2))

base_uri = "http://localhost:8081"

res = requests.delete(f'{base_uri}/subjects/users-customers-v1-value/versions/1').json()
pretty(res)
payload = { 'permanent' : 'true' }
res = requests.delete(f'{base_uri}/subjects/users-customers-v1-value/versions/1', params=payload).json()
pretty(res)