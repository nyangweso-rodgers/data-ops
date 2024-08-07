import { KafkaClient, Producer } from "kafka-node";

const kafkaClient = new KafkaClient({ kafkaHost: "kafka:29092" });
const producer = new Producer(kafkaClient);

producer.on("ready", () => {
  console.log("Kafka producer is ready.");
});

producer.on("error", (err) => {
  console.error("Error in Kafka producer:", err);
});

export { kafkaClient, producer };
