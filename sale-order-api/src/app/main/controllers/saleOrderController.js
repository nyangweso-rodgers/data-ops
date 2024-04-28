import saleOrder from "../../model/saleOrderSchema.js";

//get all sale orders
export const getSaleOrders = async (req, res) => {
  try {
    const saleOrdersData = await saleOrder.find();
    res.status(200).json(saleOrdersData);
  } catch (error) {
    console.log(error);
    res.status(500).json({ error: "Internal Server Error" });
  }
};

//get saleOrder by id
export const getSaleOrder = async (req, res) => {
  try {
    //const saleOrderData = await saleOrder.find();
    //const saleOrderData = await req.params.saleOrderData;
    const saleOrderCode = req.params.saleOrderCode; // Extract sale order code from request parameters
    const saleOrderData = await saleOrder.findOne({ code: saleOrderCode }); // Query MongoDB for the sale order by its code
    if (!saleOrderData) {
      // If no sale order with the specified code is found, return a 404 Not Found response
      return res.status(404).json({ error: "Sale order not found" });
    }
    // If the sale order is found, return it in the response
    res.status(200).json(saleOrderData);
  } catch (error) {
    console.log(error);
    res.status(500).json({ error: "Internal Server Error" });
  }
};

// create a new sale order
export const createSaleOrder = async (req, res) => {
  try {
    // Extract the order details from the request body
    const orderData = req.body;

    // Create a new order document
    const newSaleOrder = await saleOrder.create(orderData);

    // Send a success response with the newly created order
    res.status(201).json({ status: "success", data: { order: newSaleOrder } });
  } catch (error) {
    //handle any errors
    res.status(500).json({ error: "Internal Server Error!" });
  }
};

// update sale order
export const updateSaleOrder = async (req, res) => {
  try {
    // Find the sale order by ID and update its fields
    const updatedSaleOrder = await saleOrder.findByIdAndUpdate(
      req.params.id,
      req.body,
      { new: true }
    );
    // Check if the sale order exists and return the updated sale order
    if (updatedSaleOrder) {
      res.status(200).json(updatedSaleOrder);
    } else {
      res.status(404).json({ error: "Sale order not found" });
    }
  } catch (error) {
    console.log(error);
    res.status(500).json({ error: "Internal Server Error" });
  }
};

// delete sale order
export const deleteSaleOrder = async (req, res) => {
  try {
    // Find the sale order by ID and delete it
    const deletedSaleOrder = await saleOrder.findByIdAndDelete(req.params.id);

    // Check if the sale order exists and return a success message
    if (deletedSaleOrder) {
      res.status(200).json({ message: "Sale order deleted successfully" });
    } else {
      res.status(404).json({ error: "Sale order not found" });
    }
  } catch (error) {
    console.log(error);
    res.status(500).json({ error: "Internal Server Error" });
  }
};