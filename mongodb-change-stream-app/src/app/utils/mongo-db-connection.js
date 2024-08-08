import { MongoClient } from "mongodb";
import dotenv from "dotenv";

// Load environment variables from .env file
dotenv.config();

const MONGODB_URI = process.env.MONGODB_COMMUNITY_SERVER_URI_FOR_SURVEY_SERVICE;

// Define an asynchronous function to connect to MongoDB
const connectToMongoDB = async () => {
  const mongoClient = new MongoClient(MONGODB_URI);

  try {
    // Attempt to connect to the MongoDB server
    await mongoClient.connect();

    // Log a success message if connected
    console.log("Connected to MongoDB");

    // Return the database object from the client
    return mongoClient.db("myDatabase");
  } catch (error) {
    // Log an error message if connection fails
    console.error("Error connecting to MongoDB:", error);
  }
};

// Call the connectToMongoDB function and assign the returned database object to 'db'
const db = await connectToMongoDB();

export default db;