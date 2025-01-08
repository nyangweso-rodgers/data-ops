// customer-route.js

import express from "express";
import {
  createCustomerController,
  readCustomerController,
  updateCustomerController,
  deleteCustomerController,
} from "../controllers/customer-controller.js";

const router = express.Router();

router.post("/create", createCustomerController);
router.get("/read/:id", readCustomerController);
router.put("/update/:id", updateCustomerController);
router.delete("/delete/:id", deleteCustomerController); // Route to handle delete operation

export default router;
