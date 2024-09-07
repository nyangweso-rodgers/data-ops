import json
import requests

def pretty(text):
    print(json.dumps(text, indent=2))

base_uri = "http://localhost:8081"
"""
    To hard delete a schema, make two `DELETE` requests with the second request setting the permanent parameter to `true` (`/subjects/<subject>/versions/<version>?permanent=true`)
"""
res = requests.delete(f'{base_uri}/subjects/customers-value/versions/2').json()
pretty(res)
payload = { 'permanent' : 'true' }
res = requests.delete(f'{base_uri}/subjects/customers-value/versions/2', params=payload).json()
pretty(res)