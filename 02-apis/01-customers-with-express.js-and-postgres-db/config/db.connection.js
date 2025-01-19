// config/db.connection.js
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

const connectToPostgresDb = async () => {
  try {
    await prisma.$connect(); // Establish the connection
    console.log("Successfully connected to the PostgreSQL database");
  } catch (error) {
    console.error("Error connecting to the database:", error);
    process.exit(1); // Exit process with failure
  }
};

export { prisma, connectToPostgresDb };