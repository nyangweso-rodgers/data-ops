import express from "express";
import dotenv from "dotenv";

import { runConsumer } from "./src/app/consumer/customers-avro-consumer.js";

// Load environment variables from .env file
dotenv.config();

const app = express();

// Middleware to parse JSON
app.use(express.json());

// start the server
const port = process.env.APP_PORT || 3004;

const start = async () => {
  try {
    // Start the server
    // Start the Kafka Consumer
    runConsumer();
    app.listen(port, () => {
      console.log(
        `Node.js Kafka Server is running on http://localhost:${port}`
      );
    });
  } catch (error) {
    console.log("Error Starting Node.js Kafka Server:", error);
  }
};

start();
