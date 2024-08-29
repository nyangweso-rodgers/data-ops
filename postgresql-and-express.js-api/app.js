import express from "express";
import dotenv from "dotenv";

// Load environment variables from .env file
dotenv.config();

// Import routes
import updateCustomer from "./src/app/api/update-customer/route.js";
import deleteCustomer from "./src/app/api/delete-customer/route.js";

const app = express();

// Middleware to parse JSON
app.use(express.json());

// Update customer
app.put("/update-customer/:id", async (req, res) => {
  const customerId = req.params.id;
  try {
    const updatedCustomer = await updateCustomer(customerId, req.body); // Pass ID and data
    res.json(updatedCustomer); // Send the updated customer data
  } catch (error) {
    console.error(error);
    res.status(500).json({ message: "Error updating customer" });
  }
});

// Delete customer
app.delete("/delete-customer/:id", async (req, res) => {
  const customerId = req.params.id;
  try {
    await deleteCustomer(customerId); // Pass ID for deletion
    res.json({ message: "Customer deleted successfully" });
  } catch (error) {
    console.error(error);
    res.status(500).json({ message: "Error deleting customer" });
  }
});

// Start the server
const port = process.env.APP_PORT || 3004;

const start = async () => {
  try {
    // Start the server
    app.listen(port, () => {
      console.log(`Server is running on http://localhost:${port}`);
    });
  } catch (error) {
    console.log("Error starting server:", error);
  }
};

start();