// app.js
import express from "express";
import mongoose, { mongo } from "mongoose";
import dotenv from "dotenv";

import connectToMongodb from "./config/db.connection.js";

// Import routes
import v1UserRoutes from "./users/routes/v1/users.routes.js";
// Uncomment the next line if you're adding a v2 route in the future
// import v2UserRoutes from "./users/routes/v2/users.routes.js"; 

dotenv.config({path: '../../.env'}); // Load environment variables from .env file
//dotenv.config({ path: ".env" }); // Adjust the path based on your folder structure

// Connect to MongoDB
const MONGO_URI = process.env.MONGODB_URI_FOR_USERS;
console.log("MONGO_URI:", MONGO_URI); // Debugging log
connectToMongodb(MONGO_URI);


// create an express application object
const app = express();

// Middleware
app.use(express.json()); // Parse incoming JSON

// Register routes
app.use("/api/v1", v1UserRoutes); // Prefix all routes with "/api"

//create a port that the server is listening on
const PORT = process.env.PORT || 3002; //use environment variables and if not, 3002

app.listen(PORT, () => {
  console.log(`Server listening on port: ${PORT}`);
});
