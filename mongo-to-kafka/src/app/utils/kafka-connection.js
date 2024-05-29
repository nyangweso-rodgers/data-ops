// connection to kafka server
import Kafka from "kafka-node";

const kafkaHost = process.env.KAFKA_HOST;
const kafkaTopic = process.env.KAFKA_PARTICIPANTS_SERVEY_TOPIC;

const kafkaConnection = () => {
  const kafkaClient = new Kafka.KafkaClient({
    kafkaHost: kafkaHost,
  });
  const kafkaProducer = new Kafka.Producer(kafkaClient);

  kafkaProducer.on("ready", () => {
    console.log(
      `Kafka Producer is connected and ready to send messages to topic: ${kafkaTopic}`
    );
  });

  kafkaProducer.on("error", (err) => {
    console.error("Kafka producer error:", err);
  });

  return kafkaProducer;
};

export default kafkaConnection;
