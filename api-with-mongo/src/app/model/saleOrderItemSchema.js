import mongoose from "mongoose";
const { Schema, model } = mongoose;

const saleOrderItemSchema = new Schema(
  {
    item_code: {
      type: String,
      required: true,
      default: "Test Item 1",
    },
    order_qty: {
      type: Number,
      required: true,
      default: 1,
    },
    unit_price: {
      type: Number,
      required: true,
      default: 1,
    },
    order_amount: {
      type: Number,
      default: 1,
      required: true,
    },
    delivered_qty: {
      type: Number,
      default: 0,
      required: true,
    },
    returned_qty: {
      type: Number,
      default: 0,
      required: true,
    },
    item_status: {
      type: String,
      enum: [
        "CREATED",
        "PROCESSING",
        "DELIVERED",
        "PAID",
        "RETURNED",
        "EXPIRED",
      ],
      default: "CREATED",
    },
  },
  { timestamps: true }
);

//const saleOrderItem = model("saleOrderItem", saleOrderItemSchema);
export default saleOrderItemSchema;
