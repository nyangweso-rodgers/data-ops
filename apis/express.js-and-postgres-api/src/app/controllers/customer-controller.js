// customer-controller.js

import { getCustomersService } from "../services/customer-service.js";

export const getCustomerController = async (req, res) => {
  try {
    const id = req.params.id; // Assuming ID is passed as a URL parameter
    console.log("ID received:", id); // Log the ID to verify it's being received
    const customer = await getCustomersService(id);

    if (customer) {
      res.json(customer);
    } else {
      res.status(404).json({ message: "Customer not found" });
    }
  } catch (error) {
    console.error(error);
    res.status(500).json({ message: "Error getting customer" });
  }
};
