import express from "express";
import usersController from "../../controllers/users.controller.js";

const router = express.Router();

// Define user routes - Use versioned routes
router.post("/users", usersController.createUser);
router.get("/users", usersController.getAllUsers); // Get all users
router.get("/users/:id", usersController.getUsersById); // Get a specific user by ID

export default router;
