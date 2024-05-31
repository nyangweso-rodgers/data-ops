import { Sequelize } from "sequelize";
import sequelizeInstance from "../utils/customer-postgres-db-connect.js";

// Define your model directly in customerSchema.js
const CustomerSchema = sequelizeInstance.define("customers", {
  id: {
    type: Sequelize.INTEGER,
    autoIncrement: true,
    allowNull: false,
    primaryKey: true,
  },
  customer_name: { type: Sequelize.STRING, unique: false, allowNull: false },
});

export default CustomerSchema;