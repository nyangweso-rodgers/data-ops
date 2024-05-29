// src/app/index.js
import mongoose from 'mongoose';
import dotenv from "dotenv";

import mongoDBConnection from "./utils/mongo-db-connection.js";
import kafkaConnection from "./utils/kafka-connection.js";

dotenv.config();

const kafkaTopic = process.env.KAFKA_PARTICIPANTS_SURVEY_TOPIC;
const mongoURI = process.env.MONGO_URI_FOR_SURVEY_SERVICE;

const start = async () => {
  try {
    await mongoDBConnection(mongoURI);
    const kafkaProducer = kafkaConnection();

    const db = mongoose.connection;
    const participantsSurveyCollection = db.collection("participants_surveys");
    const changeStream = participantsSurveyCollection.watch();

    changeStream.on("change", (change) => {
      console.log("Detected a change in the survey collection:", change);
      const message = JSON.stringify(change.fullDocument);

      const payloads = [{ topic: kafkaTopic, messages: message }];

      kafkaProducer.send(payloads, (error, data) => {
        if (error) {
          console.log("Failed to send message to Kafka:", error);
        } else {
          console.log("Message sent to Kafka:", data);
        }
      });
    });
  } catch (error) {
    console.log("Error starting the application:", error);
  }
};

start();
