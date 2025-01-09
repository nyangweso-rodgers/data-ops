// src/app/customers/routes/v1/customers.routes.js
import express from "express";
import { createCustomer } from "../../controllers/v1/customers.controllers.js";

const router = express.Router();

// Route to create a customer
router.post("/customers", createCustomer);

export default router;
