import json
import requests

# Define the compatibility level and subject name
compatibility_level = "BACKWARD"  # or "BACKWARD", "FORWARD", "FULL"
subject_name = "users.customers.avro.v1-value"   # Value schema subject name

#base_uri = "http://localhost:8081"

customers_avro_schema_path = "../../../../../../../data-products/avro/users/customers.avsc";
# Read the schema file
with open(customers_avro_schema_path, 'r') as value_schema_file:
    schema = value_schema_file.read()

# Register the schema
value_schema_payload = {
    "schema": schema
}

register_response = requests.post(
    f'http://localhost:8081/subjects/{subject_name}/versions',
    headers={'Content-Type': 'application/vnd.schemaregistry.v1+json'},
    data=json.dumps(value_schema_payload)
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
