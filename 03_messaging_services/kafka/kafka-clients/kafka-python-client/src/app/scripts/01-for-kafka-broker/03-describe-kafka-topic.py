from confluent_kafka.admin import (AdminClient, NewTopic, ConfigResource)
import config

# Configuration
conf = {'bootstrap.servers': 'localhost:9092'}

# Initialize AdminClient
admin = AdminClient(conf)

topic_name = "users.customers.protobuf.v1";

# Get max.message.bytes property
def get_max_size(admin, topic):
    resource = ConfigResource('topic', topic)
    result_dict = admin.describe_configs([resource])
    
    # Wait for the result asynchronously
    try:
        config_entries = result_dict[resource].result()  # This is where the request is actually sent
        max_size = config_entries['max.message.bytes']
        return max_size.value
    except Exception as e:
        print(f"Failed to retrieve topic configuration: {e}")
        return None

# Main block to execute the script
if __name__ == "__main__":
    max_message_size = get_max_size(admin, topic_name)
    if max_message_size:
        print(f"Max message size for topic '{topic_name}': {max_message_size} bytes")
    else:
        print(f"Failed to retrieve the max.message.bytes property for topic '{topic_name}'")