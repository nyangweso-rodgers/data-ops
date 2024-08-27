import { Kafka } from "kafkajs";
import { SchemaRegistry } from "@kafkajs/confluent-schema-registry";

const kafka = new Kafka({
  clientId: "customers-avro-consumer",
  brokers: ["kafka:29092"],
});

const registry = new SchemaRegistry({
  host: "http://schema-registry:8081",
});

// Creating the Kafka Consumer
const customerConsumer = kafka.consumer({
  groupId: "customers-avro-group",
});

export const runConsumer = async () => {
  try {
    await customerConsumer.connect();
    console.log("Kafka Consumer connected");

    // Subscribe to the relevant topic
    await customerConsumer.subscribe({
      topic: "users.customers",
      fromBeginning: true,
    });

    // Consume messages from the topic
    await customerConsumer.run({
      eachMessage: async ({ topic, partition, message }) => {
        try {
          // Decode the Avro message using the Schema Registry
          const decodedValue = await registry.decode(message.value);
          console.log(`Received message: ${JSON.stringify(decodedValue)}`);
        } catch (error) {
          console.error("Error decoding message:", error);
        }
      },
    });
  } catch (error) {
    console.error("Error in Kafka Consumer:", error);
  }
};
