import express from "express";
import mongoose from "mongoose";
import dotenv from "dotenv";

// Load environment variables from .env file
dotenv.config();

import { router } from "./src/app/main/routes/saleOrderRoute.js";

//const MONGO_URI = `mongodb://${process.env.MONGO_USERNAME}:${process.env.MONGO_PASSWORD}@mongo:27017/admin`;

//connect to MongoDB Atlas
/**
 * connect to MongoDB Atlas
 */
/**
 * connect to MongoDB Docker Container
 */
const MONGO_URI = process.env.MONGO_URI;
//const MONGO_URI =  "mongodb://root:root@localhost:27017/sale_order_service?authSource=admin";
//const MONGO_URI='mongodb://root:root@mongo:27017/sale_order_service?authSource=admin'
//mongodb://172.30.0.3:27017?readPreference=primary&appname=MongoDB%20Compass&ssl=false

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
// Start the server
const port = 3200;
app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});
