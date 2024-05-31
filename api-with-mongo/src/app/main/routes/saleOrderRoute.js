import express from "express";

import {
  getSaleOrders,
  getSaleOrder,
  createSaleOrder,
  updateSaleOrder,
  deleteSaleOrder,
} from "../controllers/saleOrderController.js";

const router = express.Router();

//route for getting sales orders
router.get("/", getSaleOrders);

// Route for getting a sale order by its code
router.get("/:saleOrderCode", getSaleOrder); // Use "saleOrderCode" as the parameter name

// Route for creating a new sale order
router.post("/", createSaleOrder);

// Route for updating a sale order by ID
router.put("/:id", updateSaleOrder);

// Route for deleting a sale order by ID
router.delete("/:id", deleteSaleOrder);

//export default router;
export { router }; // Exporting the router object correctly
