import express from "express";
import mongoose from "mongoose";
import dotenv from "dotenv";

// Load environment variables from .env file
dotenv.config();

import { router } from "./src/app/main/routes/saleOrderRoute.js";

//connect to MongoDB Atlas

// Connect to MongoDB Docker Container using Envronment Variables
const MONGO_URI = process.env.MONGO_URI;

// Connect to MongoDB
mongoose
  .connect(MONGO_URI, {})
  .then(() => {
    console.log("Connected to MongoDB");
  })
  .catch((error) => {
    console.error("Error connecting to MongoDB:", error);
  });

// create an express application object
const app = express();

// Middleware
app.use(express.json());

// Routes
app.use(router);

const PORT = 3200;

const start = async () => {
  try {
    app.listen(PORT, () => {
      console.log(`Server is running on port ${PORT}`);
    });
  } catch (error) {
    console.log("Error starting server:", error);
  }
};

// Start the server
start();
