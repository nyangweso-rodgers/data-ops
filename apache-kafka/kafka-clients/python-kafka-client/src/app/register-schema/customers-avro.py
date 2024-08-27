import json
import requests

# Define the compatibility level and subject name
compatibility_level = "NONE"  # or "BACKWARD", "FORWARD", "FULL"
subject_name = "users.customers"  # Replace with your subject name

# Read the schema file
with open('../../../schema/customers-avro.avsc', 'r') as file:
    schema = file.read()

# Register the schema
schema_payload = {
    "schema": schema
}
register_response = requests.post(
    f'http://localhost:8081/subjects/{subject_name}/versions',
    headers={'Content-Type': 'application/vnd.schemaregistry.v1+json'},
    data=json.dumps(schema_payload)
)
print("Register Schema Response:", register_response.status_code, register_response.text)

# Set the compatibility for the subject
compatibility_payload = {
    "compatibility": compatibility_level
}
compatibility_response = requests.put(
    f'http://localhost:8081/config/{subject_name}',
    headers={'Content-Type': 'application/vnd.schemaregistry.v1+json'},
    data=json.dumps(compatibility_payload)
)
print("Set Compatibility Response:", compatibility_response.status_code, compatibility_response.text)