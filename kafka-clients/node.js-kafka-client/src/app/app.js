import express from "express";
import dotenv from "dotenv";
import kafkaProducerRoute from "../app/api/kafka-producer-router.js";

// Load environment variables from .env file
dotenv.config();

const app = express();

// Middleware to parse JSON
app.use(express.json());

// Use the Kafka producer route
app.use("/kafka", kafkaProducerRoute);

// start the server
const port = process.env.APP_PORT || 3005;

const start = async () => {
  try {
    // Start the server
    app.listen(port, () => {
      console.log(
        `Node.js Kafka Server is running on http://localhost:${port}`
      );
    });
  } catch (error) {
    console.log("Error starting Node.js Kafka Server:", error);
  }
};

start();
