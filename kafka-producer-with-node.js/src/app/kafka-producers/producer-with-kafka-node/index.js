// producer with kafka-node

import Kafka from "kafka-node";
import dotenv from "dotenv";

// Load environment variables from .env file
dotenv.config();

const kafkaHost = process.env.KAFKA_HOST;
const topic = process.env.KAFKA_TOPIC;

const user = new Kafka.KafkaClient({
  kafkaHost: kafkaHost,
});

user.on("ready", () => {
  console.log("Kafka connected successfully");
});

const producer = new Kafka.Producer(user);

producer.on("ready", () => {
  const payload = [{ topic: topic, messages: "Test message" }];

  producer.send(payload, (error, data) => {
    if (error) {
      console.error("Error in publishing message to kafka topic: ", error);
    } else {
      console.log("Message successfully published to kafka topic: ", data);
    }
  });
});

producer.on("error", (error) => {
  console.error("Producer error:", error);
});

user.on("error", (error) => {
  console.error("Error connecting to Kafka:", error);
});

// Exporting user for potential use in other files
export { user };