import express from "express";
import dotenv from "dotenv";

import sequelizeInstance  from "./src/utils/database.js"; // Import instance
import { router } from "./src/routes/customerRoute.js";

// Load environment variables from .env file
dotenv.config();

const app = express();

// Routes
app.use(router);

const PORT = process.env.PORT || 3300;

const start = async () => {
  try {
    // Perform Sequelize sync before starting the server
    await sequelizeInstance.sync();

    // Bind to all network interfaces inside the container
    app.listen(PORT, "0.0.0.0", () => {
      console.log(`Server running on http://0.0.0.0:${PORT}`);
    });
  } catch (error) {
    console.log("Error starting server:", error);
  }
};

start();
