import createCustomerService from "../services/customers-service.js";

export const createCustomerController = async (req, res) => {
  try {
    const newCustomer = await createCustomerService(req.body); // Pass only the necessary data
    res.json(newCustomer); // Send the created customer data
  } catch (error) {
    console.error(error);
    res.status(500).json({ message: "Error creating customer" });
  }
};
