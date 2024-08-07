import express from "express";
import bodyParser from "body-parser";
import { producer, kafkaClient } from "../producer/kafka-producer.js";
import { Admin } from "kafka-node";

const router = express.Router();
router.use(bodyParser.json());

const checkIfTopicExists = async (topic) => {
  return new Promise((resolve, reject) => {
    const admin = new Admin(kafkaClient);

    admin.listTopics((err, res) => {
      if (err) {
        return reject(err);
      }

      if (res[1].metadata[topic]) {
        resolve(true);
      } else {
        resolve(false);
      }
    });
  });
};

router.post("/send-message", async (req, res) => {
  const { topic, message } = req.body;

  if (!topic || !message) {
    return res.status(400).json({ error: "Topic and message are required" });
  }

  try {
    const topicExists = await checkIfTopicExists(topic);

    if (!topicExists) {
      return res.status(404).json({ error: "Topic does not exist" });
    }

    const payloads = [{ topic, messages: message }];
    console.log(`Sending payload to Kafka: ${JSON.stringify(payloads)}`);

    producer.send(payloads, (err, data) => {
      if (err) {
        console.error("Error sending message:", err);
        return res
          .status(500)
          .json({ error: "Error sending message to Kafka" });
      }
      console.log("Message sent:", data);
      res.status(200).json({ message: "Message sent successfully" });
    });
  } catch (error) {
    console.error("Error handling message sending:", error);
    res.status(500).json({ error: "Error handling message sending" });
  }
});

export default router;
