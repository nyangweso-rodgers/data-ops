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
