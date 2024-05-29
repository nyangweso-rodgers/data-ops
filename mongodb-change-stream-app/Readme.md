# Application

## Objective

- Build a **real-time application** using **MongoDB Change Streams**. The `Node.js` Application should listens for changes in a **MongoDB** collection and triggers notifications for new document insertions.

## Step 1: Connect to MongoDB

- Establish a connection to our **MongoDB** database using the appropriate driver for Node.js.

  ```js
  //src/app/utils/mongo-db-connection.js
  import { MongoClient } from "mongodb";
  import dotenv from "dotenv";

  // Load environment variables from .env file
  dotenv.config();

  const MONGO_URI = process.env.MONGO_URI_FOR_SURVEY_SERVICE;

  // Define an asynchronous function to connect to MongoDB
  const connectToMongoDB = async () => {
    const mongoClient = new MongoClient(MONGO_URI);

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
  ```

## Step 2: Create a Change Stream

- create a change stream to monitor the desired collection for insertions.

  ```js
  //src/app/index.js
  import db from "./utils/mongo-db-connection.js";

  // Access the 'notifications' collection from the connected database
  const collection = db.collection("participants_survey");

  // Create a change stream on the 'notifications' collection
  const changeStream = collection.watch();
  ```

- We access, `participants_survey` collection from the connected MongoDB database using `db.collection` method. It then creates a change stream on the `participants_survey` collection using the ‘`watch`‘ method. This **change stream** will allow the application to listen for changes in the `participants_survey` collection in real-time.

## Step 3: Listen for Changes

- Now, listen for changes in the **change stream** and handle new document insertions.

  ```js
  //src/app/index.js

  // Listen for changes in the change stream
  changeStream.on("change", (change) => {
    // Check if the change is an insertion
    if (change.type === "insert") {
      // Extract the new document from the change event
      const newParticipantSurvey = change.fullDocument;

      // Log the new notification to the console
      console.log("New Participant Survey Response", newParticipantSurvey);
    }
  });
  ```

- Here, we setup a listener for changes in the **change stream**. When a change event occurs, it checks if the operation type is an insertion (`insert`). If it is, it extracts the new document from the change event and logs it to the console as a new notification

## Step 4: Run the Application

# Resources and Further Reading
