// customer-controller.js

import {
  createCustomerService,
  readCustomersService,
  updateCustomerService,
  deleteCustomerService,
} from "../services/customer-service.js";

export const createCustomerController = async (req, res) => {
  console.log("Received Create Customer Request Body: ", req.body);
  try {
    const newCustomer = await createCustomerService(req.body);
    console.log("New Customer Successfully Created:", newCustomer); // Log successful creation
    res.json(newCustomer); // Send the created customer data
  } catch (error) {
    console.error("Error in createCustomerController:", error);
    res.status(500).json({ message: "Error creating customer" });
  }
};

export const readCustomerController = async (req, res) => {
  try {
    const id = req.params.id; // Assuming ID is passed as a URL parameter
    console.log("ID received:", id); // Log the ID to verify it's being received
    const customer = await readCustomersService(id);

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

export const updateCustomerController = async (req, res) => {
  const customerIdToUpdate = req.params.id;
  const updateCustomerData = req.body; // Get the update data from the request body
  try {
    const updatedCustomer = await updateCustomerService(
      customerIdToUpdate,
      updateCustomerData
    );
    res.json({ message: "Customer updated successfully", updatedCustomer }); // Send the updated customer data
  } catch (error) {
    console.error("updateCustomerController error: ", error);
    res.status(500).json({ message: "Error updating customer" });
  }
};

export const deleteCustomerController = async (req, res) => {
  const customerIdToDelete = req.params.id;
  try {
    const deletedCustomer = await deleteCustomerService(customerIdToDelete);
    res.json({ message: "Customer deleted successfully", deletedCustomer });
  } catch (error) {
    console.error("Error deleting customer: ", error.message);
    if (error.message === "Customer not found") {
      res.status(404).json({ message: "Customer not found" });
    } else {
      res.status(500).json({ message: "Error deleting customer" });
    }
  }
};
