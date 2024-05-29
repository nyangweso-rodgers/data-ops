import db from "./utils/mongo-db-connection.js";

// Access the 'notifications' collection from the connected database
const collection = db.collection("participants_survey");

// Create a change stream on the 'notifications' collection
const changeStream = collection.watch();

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
