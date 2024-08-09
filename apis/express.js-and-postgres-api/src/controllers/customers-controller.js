import createCustomerService from "../services/customers-service.js";

const createCustomerController = async (req, res) => {
  console.log("Received request body:", req.body); // Log request body
  try {
    const newCustomer = await createCustomerService(req.body); // Pass only the necessary data
    console.log("Customer successfully created:", newCustomer); // Log successful creation
    res.json(newCustomer); // Send the created customer data
  } catch (error) {
    console.error("Error in createCustomerController:", error);
    res.status(500).json({ message: "Error creating customer" });
  }
};

export default createCustomerController;
