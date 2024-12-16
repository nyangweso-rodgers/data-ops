// app.js
import express from "express";
import mongoose, { mongo } from "mongoose";
import dotenv from "dotenv";
import routes from "./users/routes/routes.config.js"; // Import routes

//dotenv.config(); // Load environment variables from .env file
dotenv.config({ path: ".env" }); // Adjust the path based on your folder structure

//connect to MongoDB Atlas
const MONGO_URI = process.env.MONGODB_URI_FOR_USERS;
console.log("MONGO_URI:", MONGO_URI); // Debugging log

mongoose
  .connect(MONGO_URI/*, { serverSelectionTimeoutMS: 5000 }*/)
  .then(() => console.log("Connected to MongoDB Successfully!"))
  .catch((err) => console.error("Error Connecting to MongoDB:", err));

// create an express application object
const app = express();

// Middleware
app.use(express.json()); // Parse incoming JSON

// Register routes
app.use("/api", routes); // Prefix all routes with "/api"

//create a port that the server is listening on
const PORT = process.env.PORT || 3002; //use environment variables and if not, 3002

app.listen(PORT, () => {
  console.log(`Server listening on port: ${PORT}`);
});
