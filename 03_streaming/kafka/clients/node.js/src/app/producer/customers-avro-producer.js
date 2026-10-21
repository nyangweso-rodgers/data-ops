import { Kafka, Partitioners } from "kafkajs";
import { SchemaRegistry } from "@kafkajs/confluent-schema-registry";

const kafka = new Kafka({
  clientId: "customers-avro-producer",
  brokers: ["kafka:29092"], 
});

const registry = new SchemaRegistry({
  host: "http://schema-registry:8081",
});

// Creating the Kafka Producer
const customerProducer = kafka.producer({
  createPartitioner: Partitioners.LegacyPartitioner, // Use the legacy partitioner
});

// Sending Messages to Kafka
export async function sendCustomerMessage() {
  try {
    const customerMessage = {
      id: "abc", // String
      first_name: "Rodgers", // String
      last_name: "Omondi", // String
      status: "true", // String, not boolean
      created_at: 1724763954000, // Timestamp in milliseconds, should be a long
      updated_at: 1724763954000, // Timestamp in milliseconds, should be a long
      created_by: "Rodgers", // String
      updated_by: "Rodgers", // String
    };
    console.log("Sending Customer Avro Nessage:", customerMessage);

    const topic = "users.customers";
    const id = await registry.getLatestSchemaId("users.customers-value"); // Replace with your schema name
    const encodedMessage = await registry.encode(id, customerMessage);

    const result = await customerProducer.send({
      topic: topic,
      messages: [
        {
          key: "message-key",
          value: encodedMessage,
        },
      ],
    });
    console.log("Customer Message successfully sent to kafka:", result);
  } catch (error) {
    console.error("Error sending customer message to kafka:", error);
  }
}
// Connect and Disconnect functions
export async function connectProducer() {
  await customerProducer.connect();
}

export async function disconnectProducer() {
  await customerProducer.disconnect();
}
