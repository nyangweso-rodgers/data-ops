import json
import requests

# Read the schema file
with open('../../kafka-schema/users.customers.avsc', 'r') as file:
    schema = file.read()

# Create the payload
payload = {
    "schema": schema
}

# Send the request
response = requests.post(
    'http://localhost:8081/subjects/Users-Customers/versions',
    headers={'Content-Type': 'application/vnd.schemaregistry.v1+json'},
    data=json.dumps(payload)
)

print(response.status_code, response.text)