import * as pg from "pg";
import { Sequelize } from "sequelize";

import dotenv from "dotenv";

dotenv.config();

const POSTGRES_DB = process.env.POSTGRES_TEST_DB;
const POSTGRES_USER = process.env.POSTGRES_USER;
const POSTGRES_PASSWORD = process.env.POSTGRES_PASSWORD;

const sequelizeInstance = new Sequelize(
  POSTGRES_DB,
  POSTGRES_USER,
  POSTGRES_PASSWORD,
  {
    host: process.env.PGHOST,
    dialect: "postgres",
    logging: false, // Disable sequelize logging to prevent duplicate logs
    dialectModule: pg,
  }
);

export default sequelizeInstance;
