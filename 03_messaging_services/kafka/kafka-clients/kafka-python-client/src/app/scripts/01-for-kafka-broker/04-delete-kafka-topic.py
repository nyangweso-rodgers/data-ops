from confluent_kafka.admin import AdminClient
import config

# Configuration
conf = {'bootstrap.servers': 'localhost:9092'}

# Initialize AdminClient
admin = AdminClient(conf)

topic_name = "users.avro.v1customers"

# Delete a topic and its contents
def delete_topic(admin, topic):
    try:
        result_dict = admin.delete_topics([topic])
        for topic, future in result_dict.items():
            try:
                future.result()  # The result itself is None if the operation is successful
                print(f"Topic '{topic}' and its contents have been deleted successfully.")
            except Exception as e:
                print(f"Failed to delete topic '{topic}': {e}")
    except Exception as e:
        print(f"Error deleting topic: {e}")

# Main execution block
if __name__ == "__main__":
    delete_topic(admin, topic_name)