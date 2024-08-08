import express from "express";
import dotenv from "dotenv";
import customerRoutes from "./routes/customers-route.js";

// Load environment variables from .env file
dotenv.config();

const app = express();
app.use(express.json()); // Middleware to parse JSON bodies

// Import and use routes
app.use("/api/customers", customerRoutes);

// Start the server
const port = process.env.APP_PORT || 3005;

const start = async () => {
  try {
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
