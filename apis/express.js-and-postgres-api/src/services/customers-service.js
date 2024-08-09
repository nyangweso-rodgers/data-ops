import { PrismaClient } from "@prisma/client";
const prisma = new PrismaClient();

const createCustomerService = async (customerData) => {
  console.log("New Customer Registration Data:", customerData);
  try {
    const newCustomer = await prisma.customers.create({
      data: customerData,
    });
    console.log("Customer created:", newCustomer); // Log the created customer
    return newCustomer;
  } catch (error) {
    console.error("Error in createCustomerService:", error);
    throw error; // Re-throw for handling in controller
  }
};
export default createCustomerService;
