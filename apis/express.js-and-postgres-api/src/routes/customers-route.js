import express from "express";
import createCustomerController from "../controllers/customers-controller.js";

const router = express.Router();

router.post("/create", createCustomerController); // Define route and use controller

export default router;