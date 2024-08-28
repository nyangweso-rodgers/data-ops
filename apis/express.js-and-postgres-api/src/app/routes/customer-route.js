// customer-route.js

import express from "express";
import { getCustomerController } from "../controllers/customer-controller.js";

const router = express.Router();

router.get("/read/:id", getCustomerController);

export default router;