import express from "express";
import dotenv from "dotenv";
import customerRoutes from "./src/routes/customers-route.js";
import customerRoute  from "./src/app/routes/customer-route.js";
import { PrismaClient } from "@prisma/client";
const prisma = new PrismaClient();

// Load environment variables from .env file
dotenv.config();

const app = express();
app.use(express.json()); // Middleware to parse JSON bodies

// Import and use routes
app.use("/customer", customerRoutes);
app.use("/customer", customerRoute);

// database connetion validation
async function validateDatabaseConnection() {
  // Implement your validation logic here
  // For example, try to connect to the database and catch potential errors
  try {
    const prisma = new PrismaClient();
    await prisma.$connect();
    console.log("Postgres Database connection successful");
  } catch (error) {
    console.error("Postgres Database connection failed:", error);
    throw error; // Or handle the error appropriately
  }
}

// Start the server
const port = process.env.APP_PORT || 3005;

const start = async () => {
  try {
    // Validate the database connection during startup
    await validateDatabaseConnection();

    // Start the server
    app.listen(port, () => {
      console.log(
        `Express.js and Postgresql API Server is running on http://localhost:${port}`
      );
    });
  } catch (error) {
    console.log("Error starting server:", error);
  }
};

start();
