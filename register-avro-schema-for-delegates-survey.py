import json
import requests

# Read the schema file
with open('delegates-survey.avsc', 'r') as file:
    schema = file.read()

# Create the payload
payload = {
    "schema": schema
}

# Send the request
response = requests.post(
    'http://localhost:8081/subjects/Delegates-Survey/versions',
    headers={'Content-Type': 'application/vnd.schemaregistry.v1+json'},
    data=json.dumps(payload)
)

print(response.status_code, response.text)