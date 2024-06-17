import mongoose from "mongoose";
//import { MongoClient } from "mongodb";
import dotenv from "dotenv";

// Load environment variables from .env file
dotenv.config();

const MONGODB_URI = process.env.MONGODB_ATLAS_URI_FOR_SURVEY_SERVICE;

// Log the environment variable to ensure it's loaded correctly
console.log("MONGODB_URI:", MONGODB_URI);

// check the MongoDB URI
if (!MONGODB_URI) {
  throw new Error("Define the MONGODB_URI environmental variable");
}

const connectToMongoDB = async () => {
  //const mongoClient = new MongoClient(MONGODB_COMMUNITY_SERVER_URI, { family: 4 });
  if (isConnected) {
    console.log("DB connected already");
    return;
  }
  try {
    // Attempt to connect to the MongoDB server
    await mongoose.connect(MONGODB_URI);
    //await mongoClient.connect(); //TODO: alternative connection using MongoClient

    // Log a success message if connected
    console.log("Participants Survey App Successfully Connected to MongoDB");
    isConnected = true;
  } catch (error) {
    console.log("Error Participants Survey App Connecting to MongoDB:", error);
  }
};

export default connectToMongoDB;
