import { PrismaClient } from "@prisma/client";
const prisma = new PrismaClient();

export const createCustomerService = async (customerData) => {
  console.log("New Customer Registration Data:", customerData);
  try {
    const newCustomer = await prisma.customer.create({
      data: customerData,
    });
    return newCustomer;
  } catch (error) {
    console.error(error);
    throw error; // Re-throw for handling in controller
  }
};
