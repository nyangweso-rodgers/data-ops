from confluent_kafka import Consumer, KafkaError
import fastavro
import requests
import io
import json

# configuration
schema_registry_url = "http://schema-registry:8081"
topic = 'users.customers'
group_id = 'connect-bigquery-avro-connector-for-customers'
bootstrap_servers = 'kafka:9092'

# Initialize the Kafka Consumer
consumer = Consumer({
    'bootstrap.servers': bootstrap_servers,
    'group.id': group_id,
    'auto.offset.reset': 'earliest'
})

consumer.subscribe([topic])

# Fetch schema from Schema Registry
def fetch_schema(subject, version='latest'):
    url = f"{schema_registry_url}/subjects/{subject}/versions/{version}"
    response = requests.get(url)
    response.raise_for_status()
    schema = response.json()['schema']
    return fastavro.schema.parse_schema(json.loads(schema))

# Deserialize Avro message
def deserialize_avro_message(message, schema):
    bytes_reader = io.BytesIO(message)
    reader = fastavro.reader(bytes_reader, schema=schema)
    return next(reader)

# Main loop to consume messages
try:
    schema = fetch_schema(f"{topic}-value")

    for message in consumer:
        if message.error():
            if message.error().code() == KafkaError._PARTITION_EOF:
                # End of partition
                continue
            elif message.error().code() == KafkaError._ALL_BROKERS_DOWN:
                # All brokers are down
                break
            else:
                # Other Kafka error
                print(f"Kafka error: {message.error()}")
                continue
        # Deserialize the message value
        deserialized_message = deserialize_avro_message(message.value(), schema)
        print('Received message:', deserialized_message)

finally:
    consumer.close()
