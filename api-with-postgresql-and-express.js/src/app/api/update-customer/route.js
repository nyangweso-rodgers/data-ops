import { PrismaClient } from "@prisma/client";
const prisma = new PrismaClient();

async function updateCustomer(id, data) {
  try {
    const updatedCustomer = await prisma.customer.update({
      where: { id }, // Specify where clause for identification
      data, // Data object for changes
    });
    return updatedCustomer; // Return the updated customer data
  } catch (error) {
    console.error(error);
    throw error; // Re-throw for handling in app.js
  }
}

export default updateCustomer;
