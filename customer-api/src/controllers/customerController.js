import sequelizeInstance from "../utils/database.js";
import CustomerSchema from "../models/customerSchema.js";

/**
 * CRUD controllers
 */
export const createOneCustomer = async (req, res) => {
  console.log("Create one customer: [POST] /customers/");

  try {
    const CUSTOMER_MODEL = { customer_name: req.body.customer_name };
    try {
      const customer = await CustomerSchema.create(CUSTOMER_MODEL);
      console.log("OK createOneCustomer: ", customer);

      // Send a successful response with the created customer data (optional)
      return res.status(201).json(customer);
    } catch (error) {
      console.log("Error in createOneCustomer " + "customer:", error);
      return res.status(500).json(error);
    }
  } catch (error) {
    return res.status(400).json("Bad Request");
  }
};
