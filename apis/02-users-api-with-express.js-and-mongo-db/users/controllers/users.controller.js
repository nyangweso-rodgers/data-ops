import users from "../models/users.models.js";

// create a new user
const createUser = async (req, res) => {
  try {
    const newUser = await users.create(req.body);
    res.status(201).json(newUser);
  } catch (error) {
    if (error.code === 11000) {
      res.status(400).json({ error: "Email already exists" });
    } else {
      res.status(500).json({ error: "Internal Server Error", details: error });
    }
  }
};

// Export functions
export default {
  createUser,
};
