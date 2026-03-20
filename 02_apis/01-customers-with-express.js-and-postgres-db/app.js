import express from "express";
import dotenv from "dotenv";
import v1CustomerRoutes from "./src/app/customers/routes/v1/customers.routes.js";
import { connectToPostgresDb } from "./config/db.connection.js";

// Load environment variables from .env file
dotenv.config();

const app = express();
app.use(express.json()); // Middleware to parse JSON bodies


// Register routes
app.use("/api/v1", v1CustomerRoutes); // Prefix all routes with "/api"

// Start the server
const port = process.env.APP_PORT || 3001;

const start = async () => {
  try {
    // Validate the database connection during startup
    await connectToPostgresDb();

    // Start the server
    app.listen(port, () => {
      console.log(
        `Express.js and PostgreSQL API Server is running on http://localhost:${port}`
      );
    });
  } catch (error) {
    console.log("Error starting server:", error);
  }
};

start();
