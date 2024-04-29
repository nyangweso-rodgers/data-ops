import express from "express";
import dotenv from "dotenv";

import { router } from "./src/routes/customerRoute.js";

// Load environment variables from .env file
dotenv.config();

const app = express();

// Routes
app.use(router);

const PORT = process.env.PORT;
const PGHOST = process.env.PGHOST;

const start = async () => {
  try {
    app.listen(PORT, PGHOST);
    console.log(`Running on http://${PGHOST}:${PORT}`);
  } catch (error) {
    console.log(error);
  }
};

start();
