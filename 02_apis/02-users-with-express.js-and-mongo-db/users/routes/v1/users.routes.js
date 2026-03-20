import express from "express";
import usersController from "../../controllers/v1/users.controller.js";

const router = express.Router();

// Define user routes - Use versioned routes
router.post("/users", usersController.createUser);
router.get("/users", usersController.getAllUsers); // Get all users
router.get("/users/:id", usersController.getUsersById); // Get a specific user by ID
router.put("/users/:id", usersController.updateUser); // Update user details
router.delete("/users/:id", usersController.deleteUser); // Delete a user

export default router;