# Node.js Kafka Client

## Table Of Contents

## Step: Setting Up Project Dependencies

- Navigate to the project directory and run `npm init -y` to create a `package.json` file.
- Download Dependencies by:
  ```sh
    npm i express kafka-node body-parser dotenv
  ```

## Step : Setup Kafka Producer using `kafka-node` Node.js Library

## Step : Create `test-node-js-topic` Kafka Topic

- Access the shell of the **Kafka container** by running the following command:

  ```sh
    docker exec -it kafka bash
  ```

- Create a new **kafka topic**, `test-node-js-topic` with `docker exec` command
  ```sh
    kafka-topics --create --bootstrap-server kafka:29092 --partitions 1 --replication-factor 1 --topic test-node-js-topic
  ```
- Use the `kafka-topics` command to list the **topics** in the **Kafka cluster**:
  ```sh
    #available kafka topics
    kafka-topics --list --bootstrap-server kafka:29092
  ```

## Step : Setup Kafka Consumer using `kafka-node` Node.js Library

## Step : Setup `express.js` Routes

- The router handles `POST` requests to the `/send-message` endpoint, extracting the message from the JSON data in the request body. It then creates a payloads array containing the **Kafka topic** and the message to be sent. The producer’s `send()` method is used to transmit the message to **Kafka**. If an error occurs during transmission, the router responds with a `500` status code and an error message. Otherwise, it responds with a `200` status code and a success message, indicating that the message was sent successfully.

## Step : Run the Application

## Step : Send Kafka Message

### Send Kafka Message using `curl` Command

```sh
  curl -X POST -H "Content-Type: application/json" -d '{"topic": "test-node-js-topic", "message": "Test Message with Node.js Client"}' http://localhost:3004/kafka/send-message
```

### Send Kafka Message using `POST`

# Resources and Further Reading

1. [https://examples.javacodegeeks.com/building-an-event-driven-architecture-using-kafka/#google_vignette](https://examples.javacodegeeks.com/building-an-event-driven-architecture-using-kafka/#google_vignette)
