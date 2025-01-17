// customer-service.js

import { PrismaClient } from "@prisma/client";
const prisma = new PrismaClient();

export const createCustomerService = async (newCustomerData) => {
  try {
    // Assuming 'first_name' is a unique field; adjust this to whichever field should be unique.
    /*const { first_name } = newCustomerData;

    if (!first_name) {
      throw new Error("First Name is required.");
    }

    // Check if a customer with the same first_name already exists
    const existingCustomer = await prisma.customers.findUnique({
      where: { first_name },
    });

    if (existingCustomer) {
      throw new Error("Customer with this First Name already exists.");
    }*/

    // Create the new customer if validation passes
    const createNewCustomer = await prisma.customers.create({
      data: newCustomerData,
    });
    return createNewCustomer;
  } catch (error) {
    console.error("createCustomerService Error: ", error);
  }
};

export const updateCustomerService = async (id, updateCustomerData) => {
  try {
    // Fetch the current record before updating
    const existingCustomer = await prisma.customers.findUnique({
      where: { id },
    });
    if (!existingCustomer) {
      throw new Error("Customer Id not found");
    }

    // Log the existing record
    console.log("Previous Record:", existingCustomer);

    // perform the update
    const updatedCustomer = await prisma.customers.update({
      where: { id }, // Specify where clause for identification
      data: updateCustomerData, // Data object for changes
    });
    // Log the updated record
    console.log("Updated Record:", updatedCustomer);

    return updatedCustomer; // Return the updated customer data
  } catch (error) {
    console.error("updateCustomerService error: ", error);
  }
};

export const deleteCustomerService = async (id) => {
  try {
    // Fetch the existing record before deletion
    const existingCustomer = await prisma.customers.findUnique({
      where: { id },
    });

    if (!existingCustomer) {
      throw new Error("Customer not found");
    }

    // Log the record before deletion
    console.log("Customer Record to be deleted:", existingCustomer);

    // Perform the deletion
    const deletedCustomer = await prisma.customers.delete({
      where: { id },
    });

    return deletedCustomer; // Return the deleted customer data
  } catch (error) {
    // Re-throw the error to be handled by the controller
    throw error;
  }
};
