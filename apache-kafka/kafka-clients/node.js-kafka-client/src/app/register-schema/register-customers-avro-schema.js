import { Kafka } from "kafkajs";
import {
  SchemaRegistry,
  readAVSCAsync,
} from "@kafkajs/confluent-schema-registry";

// If we use AVRO, we need to configure a Schema Registry
// which keeps track of the schema
const registry = new SchemaRegistry({
  host: "http://localhost:8081",
});

// This will create an AVRO schema from an .avsc file
const registerSchema = async () => {
  try {
    const schema = await readAVSCAsync("./avro/schema.avsc");
    const { id } = await registry.register(schema);
    return id;
  } catch (e) {
    console.log(e);
  }
};
