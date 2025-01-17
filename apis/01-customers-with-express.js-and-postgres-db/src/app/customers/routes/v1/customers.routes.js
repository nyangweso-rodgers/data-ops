// src/app/customers/routes/v1/customers.routes.js
import express from "express";
import {
  createCustomer,
  getCustomerById,
  getCustomers,
} from "../../controllers/v1/customers.controllers.js";

const router = express.Router();

// Route to create a customer
router.post("/customers", createCustomer);

// Route to get a customer by Id
router.get("/customers/:id", getCustomerById);

// Route to fetch all customers
router.get("/customers", getCustomers);

export default router;
