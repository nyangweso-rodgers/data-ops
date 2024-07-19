import { PrismaClient } from "@prisma/client";
const prisma = new PrismaClient();

async function readCustomers() {
  try {
    const allCustomers = await prisma.customer.findMany(); // Specify the model
    return allCustomers; // Return the fetched data
  } catch (error) {
    console.error(error);
    throw error; // Re-throw for handling in app.js
  }
}

export default readCustomers;