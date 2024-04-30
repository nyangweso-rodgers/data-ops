import dotenv from "dotenv";
import { Sequelize } from "sequelize";

dotenv.config();

const sequelizeInstance = new Sequelize(
  process.env.POSTGRES_DB,
  process.env.POSTGRES_USER,
  process.env.POSTGRES_PASSWORD,
  {
    host: process.env.PGHOST,
    dialect: "postgres",
    logging: false, // Disable sequelize logging to prevent duplicate logs
  }
);

export default sequelizeInstance;