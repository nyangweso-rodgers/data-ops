import { Kafka } from "kafkajs";
import {
  SchemaRegistry,
  readAVSCAsync,
} from "@kafkajs/confluent-schema-registry";

const TOPIC = "test-kafka-topic";

// configure Kafka broker
const kafka = new Kafka({
  clientId: "some-client-id",
  brokers: ["localhost:29092"],
  //essionTimeout: 300,
  //spinDelay: 100,
  //retries: 2,
});

// If we use AVRO, we need to configure a Schema Registry
// which keeps track of the schema
const registry = new SchemaRegistry({
  host: "http://localhost:8081",
});
// create a producer which will be used for producing messages
const producer = kafka.producer();

const consumer = kafka.consumer({
  groupId: "group_id_1",
});

const registerAvroSchema = async () => {
  try {
    const schema = await readAVSCAsync("./avro/schema.avsc");
    const { id } = await registry.register(schema);
    return id;
  } catch (error) {
    console.log("Error reading avro schema:", error);
  }
};

// push the actual message to kafka
const produceToKafka = async (registryId, message) => {
  await producer.connect();

  // compose the message: the key is a string
  // the value will be encoded using the avro schema
  const outgoingMessage = {
    key: message.id,
    value: await registry.encode(registryId, message),
  };

  // send the message to the previously created topic
  await producer.send({ topic: TOPIC, messages: [outgoingMessage] });

  // disconnect the producer
  await producer.disconnect();
};
