# Customer CRUD API project using Express, Docker, and PostgreSQL

## Table Of Contents

# Description

- Create a REST API, with ith Postgres, Express, and Docker Compose.

# Setup

- For project setup, check my [github.com/nyangweso-rodgers - Setting Express Development Environment With PostgreSQL Docker Container](https://github.com/nyangweso-rodgers/Programming-with-JavaScript/blob/main/03-JavaScript-Frameworks/02-Express.js/01-Setting-Express-Development-Environment/03-With-PostgreSQL-Docker-Container/Readme.md) github repo on how to setup the application with Postgres docker container.

# API Functionality

## Functionality #1: `customer-api/src/utils/database.js`

- Import `dotenv` and `Sequelize` from their respective libraries.
- Loads environment variables from the `.env` file using `dotenv.config()`.
- Creates a Sequelize instance to connect to the Postgres database using the loaded environment variables.

  ```js
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
  ```

## Functionality #2: `customer-api/src/models/customerSchema.js`

- Import `Sequelize` and the `sequelizeInstance` from `database.js`.
- Defines a `Sequelize` model named `CustomerSchema` for the "`customers`" table.
- Sets properties for the `id`, `customer_name` columns, specifying their data types and constraints.

  ```js
  import { Sequelize } from "sequelize";
  import sequelizeInstance from "../utils/database.js";

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
  ```

## Functionality #3: `customer-api/src/controllers/customerController.js`

- Imports `sequelizeInstance` and `CustomerSchema`.
- Defines an `async` function `createOneCustomer` to handle creating a new customer.
- It retrieves the customer name from the request body and attempts to create a new customer record in the database using `CustomerSchema.create`.
- Handles potential errors during creation and returns appropriate responses with error details.

  ```js
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
  ```

## Functionality #4: `customer-api/src/routes/customerRoute.js`

- Imports `express` and `bodyParser`.
- Imports the `createOneCustomer` function from `customerController.js`.
- Creates an Express `router` object.
- Configures the `router` to use `bodyParser.json()` middleware to parse `JSON` request bodies.
- Defines a `POST` route `"/"` that calls the `createOneCustomer` function.
- Exports the `router` object for use in the main application.

  ```js
  import express from "express";
  import bodyParser from "body-parser";

  import { createOneCustomer } from "../controllers/customerController.js";

  const router = express.Router();

  // Configure body-parser middleware
  router.use(bodyParser.json());

  //Add the new routes
  router.post("/", createOneCustomer);

  //export default router;
  export { router };
  ```

## Functionality #5: `customer-api/index.js`

- Imports `express` and `dotenv`.
- Imports the `router` object from `customerRoute.js`.
- Loads environment variables from the `.env` file.
- Creates an Express application instance.
- Defines a default `port` number in case the environment variable is not set.
- Uses the imported router object to define API routes.
- Defines an `async` function start to initiate the server.
- Binds the application to the specified port and logs a message upon successful startup.

  ```js
  //index.js
  import express from "express";
  import dotenv from "dotenv";

  import sequelizeInstance from "./src/utils/database.js"; // Import instance
  import { router } from "./src/routes/customerRoute.js";

  // Load environment variables from .env file
  dotenv.config();

  const app = express();

  // Routes
  app.use(router);

  const PORT = process.env.PORT || 3300;

  const start = async () => {
    try {
      // Perform Sequelize sync before starting the server
      await sequelizeInstance.sync();

      // Bind to all network interfaces inside the container
      app.listen(PORT, "0.0.0.0", () => {
        console.log(`Server running on http://0.0.0.0:${PORT}`);
      });
    } catch (error) {
      console.log("Error starting server:", error);
    }
  };

  start();
  ```

## Functionality #6: `.env` File

- Defines environment variables required for connecting to the Postgres database and setting the server port.
  ```env
    #POSTGRES
    POSTGRES_USER=rodgers
    POSTGRES_PASSWORD=<password>
    PGHOST=postgres
    PORT=3300
    POSTGRES_DB=test_db
  ```

# Dockerize the Application

## Step #1: Define `Dockerfile`

```Dockerfile
  FROM node:alpine

  # Set the working directory inside the container
  WORKDIR /app

  # Copy package.json and package-lock.json to the working directory
  COPY package*.json ./

  # Install dependencies
  RUN npm install

  # Copy the rest of the application files
  COPY . .

  # Expose port
  EXPOSE 3300

  # Command to run the application
  CMD ["npm", "start"]
```

## Step #2: Define `docker-compose.yml` File

- Defines 3 services:
  - `postgres`: Uses the official `postgres:latest` image to run a Postgres database container.
    - Exposes port 5432 for communication with the API container.
    - Mounts a volume (postgres_volume) to persist database data.
    - Uses the shared .env file for environment variables.
  - `pgadmin`: Uses the `dpage/pgadmin4` image to run a `pgAdmin` container for database management
    - Exposes port 5050 for accessing the pgAdmin interface.
    - Uses the shared .env file for environment variables (optional for PGADMIN_DEFAULT_EMAIL and PASSWORD).
    - Depends on the postgres service to ensure the database is available before starting.
  - `customer-api`: Builds the API image from the `customer-api` directory using a `Dockerfile`.
    - Uses the built image named `customer-api`.
    - Exposes port 3300 for incoming API requests.
    - Uses a specific .env file within the customer-api directory containing database connection details specific to the container.
    - Depends on the `postgres` service to ensure the database is available before starting the API.

# Test the API

## Step #: Test API with CURL

- Open your terminal or command prompt and Use the following cURL command to send a POST request to your API endpoint:

  ```sh
      curl -X POST -H "Content-Type: application/json" -d '{"customer_name": "Test customer 5"}' http://0.0.0.0:3300/
  ```

## Step #: Test API with Postman

- To check all customers, make a `GET` request:
  ```http
   http://0.0.0.0:3300/
  ```

# Resources and Further Reading

1. [github.com/nyangweso-rodgers - Setting Express.js Development Environment](https://github.com/nyangweso-rodgers/Programming-with-JavaScript/blob/main/03-JavaScript-Frameworks/02-Express.js/01-Setting-Express-Development-Environment/Readme.md)
2. [github.com/nyangweso-rodgers - Docker-Commands](https://github.com/nyangweso-rodgers/My-Journey-Into-Computer-Science/blob/master/04-VMs-vs-Containers/02-Containers/01-Docker/01-Docker-Commands/Readme.md)
3. [github.com/nyangweso-rodgers - Docker Compose File](https://github.com/nyangweso-rodgers/My-Journey-Into-Computer-Science/blob/master/04-VMs-vs-Containers/02-Containers/01-Docker/02-Docker-Compose-File/Readme.md)
4. [sequelize.org/docs/v6/](https://sequelize.org/docs/v6/)
