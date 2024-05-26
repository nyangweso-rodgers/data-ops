# Project Setup

- Set up a new node project and install these two dependencies. The **schema registry** is required to work with `AVRO` schemas.

  ```sh
      npm i kafkajs @kafkajs/confluent-schema-registry
  ```

# Configuring the Kafka connection

- First import all the dependencies and configure all **Kafka** related settings.
