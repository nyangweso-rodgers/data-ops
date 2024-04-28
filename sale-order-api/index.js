import express from "express";
import mongoose from "mongoose";
import dotenv from "dotenv";

import {router } from "./src/app/main/routes/saleOrderRoute.js";

dotenv.config(); // Load environment variables from .env file

//connect to MongoDB Atlas
const MONGO_URI = process.env.MONGO_URI;

// create an express application object
const app = express();

// Middleware
app.use(express.json());

// Routes
app.use(router);

// Connect to MongoDB
mongoose
  .connect(MONGO_URI, {})
  .then(() => {
    console.log("Connected to MongoDB");
  })
  .catch((err) => {
    console.error("Error connecting to MongoDB:", err);
  });

// Start the server
const port = 3200;
app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});
