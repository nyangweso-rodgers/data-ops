import { PrismaClient } from "@prisma/client";
const prisma = new PrismaClient();

async function createCustomer(req) {
  const customerData = req.body; // Assuming data is in request body
  console.log("Received customer data:", customerData);
  try {
    const newCustomer = await prisma.customer.create({ data: customerData }); // Pass data object
    return newCustomer; // Return the created customer data
  } catch (error) {
    console.error(error);
    throw error; // Re-throw for handling in app.js
  }
}
export default createCustomer;
