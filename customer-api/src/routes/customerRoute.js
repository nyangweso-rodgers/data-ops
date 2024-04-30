import express from "express";
import bodyParser from "body-parser";

import { createOneCustomer } from "../controllers/customerController.js";

const router = express.Router();

// Configure body-parser middleware
router.use(bodyParser.json());

//Add the new routes
router.post("/", createOneCustomer);

//export default router;
export { router };
