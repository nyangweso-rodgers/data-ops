# Node.js Kafka Client

## Table Of Contents

## Step: Setting Up Project Dependencies

- Navigate to the project directory and run `npm init -y` to create a `package.json` file.
- Download Dependencies by:
  ```sh
    npm i express kafka-node body-parser dotenv
  ```

## Step : Setup Kafka Producer using `kafka-node` Node.js Library

## Step : Setup Kafka Consumer using `kafka-node` Node.js Library

## Step : Setup `express.js` Routes

- The router handles `POST` requests to the `/send-message` endpoint, extracting the message from the JSON data in the request body. It then creates a payloads array containing the **Kafka topic** and the message to be sent. The producer’s `send()` method is used to transmit the message to **Kafka**. If an error occurs during transmission, the router responds with a `500` status code and an error message. Otherwise, it responds with a `200` status code and a success message, indicating that the message was sent successfully.

## Step : Run the Application

## Step : Send Kafka Message

### Send Kafka Message using `curl` Command

```sh
  curl -X POST -H "Content-Type: application/json" -d '{"topic": "test-topic", "message": "Hello, Kafka!"}' http://localhost:3004/kafka/send-message
```

### Send Kafka Message using `POST`

# Resources and Further Reading

1. [https://examples.javacodegeeks.com/building-an-event-driven-architecture-using-kafka/#google_vignette](https://examples.javacodegeeks.com/building-an-event-driven-architecture-using-kafka/#google_vignette)
