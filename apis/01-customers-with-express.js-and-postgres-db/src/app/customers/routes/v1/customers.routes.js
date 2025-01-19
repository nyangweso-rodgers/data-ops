// src/app/customers/routes/v1/customers.routes.js
import express from "express";
import {
  createCustomer,
  getCustomerById,
  getCustomers,
  updateCustomerById,
  deleteCustomerById,
} from "../../controllers/v1/customers.controllers.js";

const router = express.Router();

// Route to create a customer
router.post("/customers", createCustomer);

// Route to get a customer by Id
router.get("/customers/:id", getCustomerById);

// Route to fetch all customers
router.get("/customers", getCustomers);

// Route to update a customer by ID
router.put("/customers/:id", updateCustomerById);

// Route to delete a customer by ID
router.delete("/customers/:id", deleteCustomerById);

export default router;
