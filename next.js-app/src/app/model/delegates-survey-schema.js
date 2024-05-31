import * as pg from 'pg';
import { Sequelize } from "sequelize";

import sequelizeInstance from "../utils/delegates-survey-postgres-db-connect.js";

// Define your model directly in customerSchema.js
const DelegatesSurveySchema = sequelizeInstance.define("delegates_survey", {
  id: {
    type: Sequelize.INTEGER,
    autoIncrement: true,
    allowNull: false,
    primaryKey: true,
  },
  first_name: { type: Sequelize.STRING, unique: false, allowNull: false },
  last_name: { type: Sequelize.STRING, unique: false, allowNull: false },
  company_name: { type: Sequelize.STRING, allowNull: false },
});

export default DelegatesSurveySchema;
