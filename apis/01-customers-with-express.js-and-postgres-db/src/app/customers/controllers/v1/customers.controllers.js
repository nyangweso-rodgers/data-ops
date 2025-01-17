// src/app/customers/controllers/v1/customers.controllers.js
//import { prisma } from "../../../../../config/db.connection"; // Use shared Prisma instance
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

// Create new customer
export const createCustomer = async (req, res) => {
  try {
    const { first_name, last_name, status, created_by, updated_by } = req.body;

    const newCustomer = await prisma.customers.create({
      data: {
        first_name,
        last_name,
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
