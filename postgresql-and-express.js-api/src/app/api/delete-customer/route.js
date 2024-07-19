import { PrismaClient } from "@prisma/client";
const prisma = new PrismaClient();

async function deleteCustomer(id) {
  try {
    // Fetch the customer before deletion to log details
    const customerToDelete = await prisma.customer.findUnique({
      where: { id },
    });
    if (!customerToDelete) {
      throw new Error(`Customer with ID ${id} not found`);
    }
    console.log("Deleting customer:", customerToDelete);

    // Perform deletion
    await prisma.customer.delete({
      where: {
        id, // Use destructuring for cleaner syntax
      },
    });
    return { message: "Customer deleted successfully", deletedCustomer: customerToDelete }; // Optional response
  } catch (error) {
    console.error(error);
    throw error; // Re-throw for handling in app.js
  }
}

export default deleteCustomer;
