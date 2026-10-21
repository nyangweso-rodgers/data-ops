# Java Kafka Client

## Table Of Contents

# Description

- For a **Spring Boot service** that reads data from a **Kafka topic**, deserializes Protobuf messages, and writes the data to Google BigQuery, you’ll typically have several components working together. These include `DTOs`, `mappers`, and `services` responsible for streaming data and interacting with external systems.

# Architecture Overview

1. **Kafka Consumer**: Listens to a Kafka topic and consumes messages.
2. **Protobuf Deserialization**: Converts Kafka’s binary Protobuf message into a usable DTO.
3. **Mapper**: Transforms the DTO (or Protobuf data) into the appropriate format for BigQuery (if schema transformation is needed).
4. **BigQuery Sink Service**: Writes the transformed data to a BigQuery table.

# Setting Up Kafka and Spring Boot

- To get started with Kafka and Spring Boot, follow these steps:

## Step 1. Run Kafka and Zookeeper

- Download and start the Kafka server. You’ll need both Kafka and Zookeeper running.

## Step 2. Add Dependencies

- Add Dependencies: Add the Kafka and Spring Boot dependencies to your `pom.xml` or `build.gradle` file.

# Creating a Kafka Producer in Spring Boot

- Let’s create an Order Service that produces events to Kafka whenever a new order is placed. In this example, the Order Service publishes an “Order Created” event to a Kafka topic.
- Kafka Configuration:
  - Configure the Kafka properties in `application.yml`
    ```yml
    spring:
      kafka:
        bootstrap-servers: localhost:9092
        producer:
          key-serializer: org.apache.kafka.common.serialization.StringSerializer
          value-serializer: org.apache.kafka.common.serialization.StringSerializer
    ```
- Producer Service:

  - Create a `KafkaProducerService` class that sends messages to **Kafka**

    ```java
        import org.springframework.kafka.core.KafkaTemplate;
        import org.springframework.stereotype.Service;

        @Service
        public class KafkaProducerService {
                private final KafkaTemplate<String, String> kafkaTemplate;

        public KafkaProducerService(KafkaTemplate<String, String> kafkaTemplate) {
            this.kafkaTemplate = kafkaTemplate;
        }

        public void sendOrderEvent(String orderId) {
            kafkaTemplate.send("order-topic", orderId);
            System.out.println("Order event sent for order ID: " + orderId);
        }
        }
    ```

    - Here, we use `KafkaTemplate` to send messages to a Kafka topic. When an order is created, `sendOrderEvent` sends the `orderId` to the “`order-topic`” topic.

# Creating a Kafka Consumer in Spring Boot

- Other services, like the Inventory Service, can subscribe to “`order-topic`” and react to new events.
- **Consumer Configuration**
  - Add consumer properties to `application.yml`
    ```yml
    spring:
      kafka:
        consumer:
          group-id: inventory-group
          key-deserializer: org.apache.kafka.common.serialization.StringDeserializer
          value-deserializer: org.apache.kafka.common.serialization.StringDeserializer
    ```
- **Consumer Service**

  - Create a `KafkaConsumerService` class to listen to events.

    ```java
        import org.apache.kafka.clients.consumer.ConsumerRecord;
        import org.springframework.kafka.annotation.KafkaListener;
        import org.springframework.stereotype.Service;

        @Service
        public class KafkaConsumerService {
            @KafkaListener(topics = "order-topic", groupId = "inventory-group")
            public void processOrderEvent(ConsumerRecord<String, String> record) {
                String orderId = record.value();
                System.out.println("Received order event for order ID: " + orderId);
                // Update inventory based on the new order
            }
        }
    ```

    - With `@KafkaListener`, this service consumes messages from the “order-topic” topic and processes each event.

# Handling Event Reliability

- In real-world applications, it’s crucial to ensure message reliability. **Kafka** provides mechanisms for this, including acknowledgments and retries.
- **Acknowledgments**
  - You can set acknowledgments (`acks`) to `all` for stronger durability guarantees
    ```yml
    spring:
      kafka:
        producer:
          acks: all
    ```
- **Retries and Error Handling**
  - Configure retries to handle temporary failures
    ```yml
    spring:
      kafka:
        consumer:
          enable-auto-commit: false
          max-poll-records: 10
        listener:
          ack-mode: manual
    ```

# Resources and Further Reading

1. [https://www.javacodegeeks.com/2024/10/event-driven-microservices-with-spring-boot-kafka.html#google_vignette](https://www.javacodegeeks.com/2024/10/event-driven-microservices-with-spring-boot-kafka.html#google_vignette)
