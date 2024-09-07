
from confluent_kafka.admin import (AdminClient, NewTopic, ConfigResource)
import config

# Configuration
conf = {'bootstrap.servers': 'localhost:9092'}

# Initialize AdminClient
admin = AdminClient(conf)

topic_name = "users.customers.protobuf.v1";
# return True if topic exists and False if not
def topic_exists(admin, topic):
    try:
        metadata = admin.list_topics(timeout=10) # Set a timeout of 10 seconds
        for t in iter(metadata.topics.values()):
            if t.topic == topic:
                return True
        return False
    except Exception as e:
        print(f"Error retrieving topics: {e}")
        return False

# Main block
if __name__ == "__main__":
    if topic_exists(admin, topic_name):
        print(f"Topic '{topic_name}' already exists.")
    else:
        print(f"Topic '{topic_name}' does not exist.")