import mongoose from "mongoose";
import dotenv from "dotenv";

// Load environment variables from .env file
dotenv.config();

const MONGO_URI = process.env.MONGO_URI_FOR_SURVEY_SERVICE;

// Log the environment variable to ensure it's loaded correctly
console.log("MONGO_URI:", MONGO_URI);

const mongoDBConnect = async () => {
  try {
    await mongoose.connect(MONGO_URI);
    console.log("App Successfully Connected to MongoDB");
  } catch (error) {
    console.log("Error connecting to MongoDB:", error);
  }
};

export default mongoDBConnect;
