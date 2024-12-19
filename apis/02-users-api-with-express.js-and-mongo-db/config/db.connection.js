import mongoose from "mongoose";

const connectToMongodb = async (mongoUri) => {
  try {
    await mongoose.connect(mongoUri /*, { serverSelectionTimeoutMS: 5000 }*/);
    console.log("Connected to MongoDB Successfully!");
  } catch (error) {
    console.error("Error Connecting to MongoDB:", error);
    process.exit(1); // Exit the process if the connection fails}
  }
};

export default connectToMongodb;