import usersModel from "../models/users.models.js";

// create a new user
const createUser = async (req, res) => {
  try {
    const newUser = await usersModel.create(req.body);
    // Log success to Docker container logs
    console.log(`User created successfully: ${newUser}`);

    // Respond to the client
    res.status(201).json({
      message: "User created successfully",
      user: newUser,
    });
  } catch (error) {
    if (error.code === 11000) {
      // Log error to Docker container logs
      console.error(
        `Failed to create user: Email already exists (${req.body.email})`
      );

      // Respond to the client
      res.status(400).json({ error: "Email already exists" });
    } else {
      // Log error details to Docker container logs
      console.error("Failed to create user: Internal Server Error", error);

      // Respond to the client
      res.status(500).json({ error: "Internal Server Error", details: error });
    }
  }
};

// Get all users
const getAllUsers = async (req, res) => {
  try {
    const users = await usersModel.find().select("-password"); // Exclude password field
    res.status(200).json(users);
  } catch (error) {
    console.error("Failed to fetch users:", error);
    res.status(500).json({ error: "Internal Server Error", details: error });
  }
};

// Get a specific user by ID
const getUsersById = async (req, res) => {
  try {
    const user = await usersModel.findById(req.params.id).select("-password"); // Exclude password field
    if (!user) {
      return res.status(404).json({ error: "User not found" });
    }
    res.status(200).json(user);
  } catch (error) {
    console.error("Failed to fetch user by ID:", error);
    res.status(500).json({ error: "Internal Server Error", details: error });
  }
};

// Export functions
export default {
  createUser,
  getAllUsers,
  getUsersById,
};
