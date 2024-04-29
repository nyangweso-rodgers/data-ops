import dotenv from "dotenv";
import { Sequelize } from "sequelize";

dotenv.config();

const sequelizeInstance = new Sequelize(
  //process.env.PGDATABASE,
  process.env.POSTGRES_CUSTOMER_SERVICE_DB,
  //process.env.PGUSER,
  process.env.POSTGRES_USER,
  //process.env.PGPASSWORD,
  process.env.POSTGRES_PASSWORD,
  { host: process.env.PGHOST, dialect: "postgres" }
);
export default sequelizeInstance;