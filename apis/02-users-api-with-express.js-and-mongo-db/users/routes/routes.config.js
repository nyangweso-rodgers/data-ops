import express from "express";
import usersController from "../controllers/users.controller.js";

const router = express.Router();

// Define user routes
router.post("/users", usersController.createUser);

export default router;