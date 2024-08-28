// customer-service.js

import { PrismaClient } from "@prisma/client";
const prisma = new PrismaClient();

export const getCustomersService = async (id) => {
  // Ensure 'id' is received as a parameter
  try {
    const getCustomerById = await prisma.customers.findUnique({
      where: { id },
    });
    return getCustomerById;
  } catch (error) {
    console.error(error);
  }
};
