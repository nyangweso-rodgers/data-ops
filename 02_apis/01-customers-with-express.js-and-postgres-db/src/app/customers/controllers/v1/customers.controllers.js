// src/app/customers/controllers/v1/customers.controllers.js
//import { prisma } from "../../../../../config/db.connection"; // Use shared Prisma instance
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

// Create new customer
export const createCustomer = async (req, res) => {
  try {
    const {
      first_name,
      last_name,
      phone_number,
      email,
      status,
      created_by,
      updated_by /**  ... other fields */,
    } = req.body;

    // 1. Validate required fields
    // Check for mandatory fields
    if (!first_name || !last_name || !phone_number || !email) {
      return res.status(400).json({
        error:
          "Missing mandatory fields: first_name and last_name are required",
      });
    }
    /*
    // 2. Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return res.status(400).json({ message: "Invalid email format." });
    }
    */

     
    // 3. Check email uniqueness
    const existingCustomer = await prisma.customers.findUnique({
      where: { email },
    });

    if (existingCustomer) {
      return res.status(400).json({ error: 'Email already exists' });
    }

    const newCustomer = await prisma.customers.create({
      data: {
        first_name,
        last_name,
        phone_number,
        email,
        status: status ?? true, // Default to true if not provided
        created_by: created_by ?? "rodgerso65@gmail.com", // Default email
        updated_by: updated_by ?? "rodgerso65@gmail.com", // Default email
      },
    });

    console.log("New Customer Successfully Created:", newCustomer); // Log successful creation
    res.status(201).json(newCustomer); // Send the created customer data
  } catch (error) {
    console.error("Error Creating Customer:", error);
    res
      .status(500)
      .json({ error: "An error occurred while creating the customer" });
  }
};

// fetch customer by id
export const getCustomerById = async (req, res) => {
  // Ensure 'id' is received as a parameter
  try {
    // Extract the 'id' from request parameters
    const id = req.params.id;

    // Validate that 'id' is provided and is not an empty string
    if (!id || id.trim() === "") {
      throw new Error("Invalid customer ID");
    }
    // Fetch the customer by ID
    const customer = await prisma.customers.findUnique({
      where: { id },
    });
    // Check if the customer exists
    if (!customer) {
      return res.status(404).json({ error: "Customer not found" });
    }
    // Log the customer ID to the console
    console.log(`Customer fetched successfully. ID: ${id}`);

    // Respond with the customer data
    return res.status(200).json(customer);
  } catch (error) {
    console.log("Error fetching customer:", error);

    // Send a generic error response
    return res.status(500).json({ error: "Internal Server Error" });
  }
};

// fetch customers
export const getCustomers = async (req, res) => {
  try {
    // Fetch all customers from the database
    const customers = await prisma.customers.findMany();

    // Log the number of customers fetched
    console.log(`Fetched ${customers.length} customers successfully.`);

    // Send the customers data as a response
    return res.status(200).json(customers);
  } catch (error) {
    // Log the error to the console
    console.error("Error fetching customers:", error.message);

    // Send an error response
    return res.status(500).json({ error: "Failed to fetch customers" });
  }
};

// update customer by id

export const updateCustomerById = async (req, res) => {
  try {
    const { id } = req.params;
    const { first_name, status } = req.body;

    // Check if any fields are actually provided for update
    const hasUpdates = first_name || status !== undefined;
    if (!hasUpdates) {
      console.log("No fields provided for update");
      return res.status(400).json({ message: "No fields provided for update" });
    }

    // Sanitize input fields
    const sanitizedData = {
      first_name: first_name?.trim(),
      status: status,
    };

    // Fetch the current record before updating
    const customer = await prisma.customers.findUnique({
      where: { id },
    });

    if (!customer) {
      return res.status(404).json({ message: "Customer Id not found" });
    }
    // Log the existing record
    console.log("Original Customer Record:", customer);

    // Construct the update data object
    const updateData = {};
    if (sanitizedData.first_name)
      updateData.first_name = sanitizedData.first_name;
    if (sanitizedData.status !== undefined)
      updateData.status = sanitizedData.status;

    // Perform the update
    const updatedCustomer = await prisma.customers.update({
      where: { id },
      data: updateData,
    });

    // Log the updated record
    console.log("Updated Customer Record:", updatedCustomer);

    res.status(200).json(updatedCustomer);
  } catch (error) {
    console.error("Error updating customer:", error.message);

    // Handle errors and send appropriate response
    return res.status(500).json({ error: "Failed to update customer" });
  }
};

// delete customer by id
export const deleteCustomerById = async (req, res) => {
  try {
    const { id } = req.params;

    // Find the customer by ID
    const customer = await prisma.customers.findUnique({
      where: { id },
    });

    // If customer not found, return 404 Not Found
    if (!customer) {
      return res.status(404).json({ message: "Customer not found" });
    }

    // Delete the customer
    const deletedCustomer = await prisma.customers.delete({
      where: { id },
    });

    // You can now use the deletedCustomer object if needed.
    // For example, you could log it:
    console.log("Deleted Customer:", deletedCustomer);

    // Send success response
    res.status(200).json({ message: "Customer deleted successfully" });
  } catch (error) {
    console.error("Error deleting customer:", error);
    res.status(500).json({ message: "Internal Server Error" });
  }
};
