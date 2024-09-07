# create kafka topic

from confluent_kafka.admin import (AdminClient, NewTopic, ConfigResource)
import config

# Configuration
conf = {'bootstrap.servers': 'localhost:9092'}

# Initialize AdminClient
admin = AdminClient(conf)

topic_name = "users.customers.avro.v1";

# Check if topic exists
def topic_exists(admin, topic):
    try:
        metadata = admin.list_topics(timeout=10)  # Timeout after 10 seconds
        return topic in metadata.topics
    except Exception as e:
        print(f"Error checking topic existence: {e}")
        return False

# create new topic and return results dictionary
def create_topic(admin, topic):
    new_topic = NewTopic(topic, num_partitions=1, replication_factor=1) 
    result_dict = admin.create_topics([new_topic])
    for topic, future in result_dict.items():
        try:
            future.result()  # The result itself is None
            print("Topic {} created".format(topic))
        except Exception as e:
            print("Failed to create topic {}: {}".format(topic, e))
# Main execution block
if __name__ == "__main__":
    if topic_exists(admin, topic_name):
        print(f"Topic '{topic_name}' already exists.")
    else:
        print(f"Topic '{topic_name}' does not exist. Creating it now...")
        create_topic(admin, topic_name)