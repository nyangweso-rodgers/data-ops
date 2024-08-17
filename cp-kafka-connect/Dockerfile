# Start from the Confluent Kafka Connect base image
FROM confluentinc/cp-kafka-connect:7.7.0

# Copy the plugins to the correct location
COPY plugins/ /usr/share/java/

# Ensure the plugin path is set
ENV CONNECT_PLUGIN_PATH="/usr/share/java,/usr/share/confluent-hub-components"

# Command to start Kafka Connect
CMD ["connect-distributed", "/etc/kafka/connect-distributed.properties"]