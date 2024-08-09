# API with Node.js, Express.js and PostgreSQL

## Table Of Contents

# Project Structure

1. `app.js`: The main entry point for the Express application, where the Express app is set up and middlewares, routes, etc., are applied.
2. `prisma/`: Contains the Prisma schema and migration files.
3. `src/`: The source code directory
   1. `controllers/`: Contains controller files, which handle **requests** and **responses**.
   2. `routes/`: Defines the application's routes, linking them to the corresponding **controllers**.
   3. `services/`: Contains business logic and service files that interact with the database through **Prisma**.
   4. `middleware/`
4. `config/` directory holds configuration files for your application, such as database connections, server settings, and environment variables.
5. `utils/`: Utility functions and helper modules are stored in the `utils/` directory. These functions perform common tasks like **validation** and formatting that are used throughout the application.

# Project Structure Description

## 1. `app.js`

- The `app.js` file is the entry point of your application. It’s where you initialize the **Express app**, set up **middleware**, define **routes**, and start the server. Think of it as the control center of your web application.

  ```js
  const express = require("express");
  const app = express();
  const config = require("./config");
  const routes = require("./routes");

  // Middleware setup
  app.use(express.json());

  // Routes setup
  app.use("/api", routes);

  // Start server
  const PORT = config.port || 3000;
  app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
  });

  module.exports = app;
  ```

## 2. `src/controllers/`

- **Role**: **Controllers** handle HTTP **requests** and **responses**. They are responsible for:
  1. Receiving HTTP requests from the client.
  2. Passing data to the appropriate service or business logic.
  3. Returning the appropriate **response** to the client.
- Each file in the **controllers** directory typically corresponds to a different part of your application (e.g., **customers**, **products**).
- Example (`controllers/customers-controllers.js`):

  ```js
  import createCustomerService from "../services/customers-service.js";

  async function createCustomerController(req, res) {
    console.log("Received request body:", req.body);
    try {
      const newCustomer = await createCustomerService(req.body);
      console.log("Customer successfully created:", newCustomer);
      res.json(newCustomer);
    } catch (error) {
      console.error("Error in createCustomerController:", error);
      res.status(500).json({ message: "Error creating customer" });
    }
  }

  export default createCustomerController;
  ```

  - Here:
    - Request Handling: Parse the request `body`, `headers`, and query parameters.
    - Response Handling: Send back the response, including status codes and data.
    - Error Handling: Catch errors and return appropriate HTTP error responses.

## 3. `src/services/`

- **Role**: **Services** contain the business logic and interact with the data layer or other external services. They are responsible for:

  1. Performing core business operations.
  2. Interacting with databases or other external systems.
  3. Returning data to controllers.

- Example (```src/services/customers-service.js`)

  ```js
  import { PrismaClient } from "@prisma/client";

  const prisma = new PrismaClient();

  async function createCustomerService(customerData) {
    console.log("New Customer Registration Data:", customerData);
    try {
      const newCustomer = await prisma.customers.create({
        data: customerData,
      });
      console.log("Customer created:", newCustomer);
      return newCustomer;
    } catch (error) {
      console.error("Error in createCustomerService:", error);
      throw error;
    }
  }

  export default createCustomerService;
  ```

  - Here:
    - Business Logic: Implement the core functionality and rules of the application.
    - Data Access: Interact with the database or other services to fetch, update, or delete data.
    - Error Handling: Handle and possibly log errors related to business operations.

## 4. `src/routes/`

- **Routes** define the paths to different parts of your application and map them to the appropriate **controllers**.
- Example (`routes/api.js`):

  ```js
  const express = require("express");
  const router = express.Router();
  const customerController = require("../controllers/customer");

  router.get("/customers", customerController.getAllCustomers);

  module.exports = router;
  ```

## `src/middleware/`

- **Middleware** functions are used to process requests before they reach the **controllers**. They can handle tasks like **authentication**, **logging**, and request validation.
- Example (`middleware/auth.js`):

  ```js
  module.exports = (req, res, next) => {
    const token = req.header("Authorization");
    if (!token) return res.status(401).json({ message: "Access Denied" });

    try {
      const verified = jwt.verify(token, process.env.JWT_SECRET);
      req.user = verified;
      next();
    } catch (err) {
      res.status(400).json({ message: "Invalid Token" });
    }
  };
  ```

# Setup

## Step 1: Install npm packages

- Initialize Node.js environment by running:
  ```sh
    npm init -y
  ```
- Next We will install the required dependencies:
  ```sh
    npm i --save-dev prisma
  ```

## Step 2: Setup Prisma ORM

### Step 2.1: Installing the Prisma Client

- The Client is essentially all of the code for interacting to our database.
- To start using **Prisma**, you will need the `prisma` and `@prisma/client` packages.
- `prisma` is the **Prisma CLI** tool while `@prisma/client` is an auto-generated query builder that will help you query your database.

  ```sh
    npm i prisma @prisma/client # instal these at the root of your project application
  ```

- To use the **Prisma Client**, We have to add the following code:
  ```js
  import { PrismaClient } from "@prisma/client";
  const prisma = new PrismaClient();
  ```

### Step 2.2: Initialize Prisma

- Now, We'll Initialize our **Prisma** by:
  ```sh
      npx prisma init
  ```
- We can also specify the database during **Prisma** initialization. For this Project, We are using **PostgreSQL** so the Command will be:
  ```sh
      npx prisma init --datasource-provider postgresql
  ```
- These steps will generate essential configuration and setup files for our project.
- **Remarks**:
  - After you change your **data model**, you'll need to manually re-generate **Prisma Client** to ensure the code inside `node_modules/.prisma/client` gets updated:
    ```sh
      npx prisma generate
    ```

### Step 2.3: Prisma Model Setup

- Here, we'll define the **Customer Model** for our application in the `schema.prisma` file.
- If you decide to work with the code-first approach, you can use [Prisma Migrate](https://www.prisma.io/docs/orm/prisma-migrate) to create the tables in your database. Start by writing your **schema definition** using Prisma's markup language.

  ```prisma
    model Customer {
        id String @id @default(uuid())
        first_name String
        last_name String
        status     Status  @default(TRUE)
        created_at DateTime @default(now())
        updated_at DateTime @updatedAt
        created_by String @default("rodgerso65@gmail.com")
        updated_by String @default("rodgerso65@gmail.com")
        created_by_name String @default("Rodgers Nyangweso")
        updated_by_name String @default("Rodgers Nyangweso")


        @@map("customer") // This will ensure the table name is lowercase "customer"
        }
        enum Status {
        TRUE
        FALSE
        }
  ```

- With your **schema** set up, you can prepare your database by selecting one of the providers supported by **Prisma**. In the example below, I'm using **PostgreSQL**, but there are several available options like MySQL, SQLite, MongoDB, CockroachDB, and Microsoft SQL Server:
  ```prisma
    datasource db {
        provider = "postgresql"
        url      = env("DATABASE_URL")
    }
    generator client {
        provider = "prisma-client-js"
        }
  ```
- It's just that simple. If you switch from PostgreSQL to MySQL (or any other provider), change your provider and rebuild your migration. If you need to create seed data, you can configure your application to know where your seed data is and use the Prisma client to insert any data you need.

### Step 2.4: Adding the Connection URL

- You need a **connection URL** to connect `prisma` to your **PostgreSQL database**. The general format for a connection URL is:
  ```sh
    postgres://{username}:{password}@{hostname}:{port}/{database-name}
  ```
- Example:
  ```sh
    #.env
    POSTGRES_TEST_DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${PGHOST}:${PORT}/${POSTGRES_TEST_DB}"
  ```
- Then in `schema.prisma`, specify the **database connection URL**:

  ```prisma
    datasource db {
      provider = "PostgreSQL"
      url      = env("POSTGRES_USERS_DATABASE_URL")
      }

  ```

### Step 2.5: Prisma Migration

- **Prisma Migrate** is a database migration tool that supports the model/ entity-first migration pattern to manage database schemas in your **local environment** and in **production**.
- How to get started with migrating your **schema** in a development environment using **Prisma Migrate**.
  1. Create the first migration:
     ```sh
      prisma migrate dev --name init
     ```
     - Your **Prisma schema** is now in sync with your database schema and you have initialized a migration history:
  2.
- Till now **Prisma** and our database is completely separate! They are able to interact with each other but defining something in **prisma** won't do anything in the database!
- Suppose We made changes to our **schema**, To reflect those changes in our DB, we have to **migrate** our new **schema**! For that we have to use a command:
  ```sh
      npx prisma migrate dev --name init
  ```
- After that, It will create a migration file. This migration file will communicate with our postgres database.

### Step 2.6: CRUD Operations with Prisma Client

- Create an `app.js` file and start implementing CRUD!
  ```javascript
  import { PrismaClient } from "@prisma/client";
  const prisma = new PrismaClient();
  ```

# Step 3: Define API Endpoints:

1. Use `app.post` for creating new customers (`/create-customer`).
2. Use `app.get` for fetching all customers (`/read-customers`).
3. Use `app.put` for updating existing customers (`/update-customer/:id`).
4. Use `app.delete` for deleting customers (`/delete-customer/:id`).

## Step : Dockerize the Application

### Step : Running the Container

- Run the application by:

  ```bash
      docker-compose up -d --build api-with-postgresql-and-express.js
  ```

- This starts a container from the my-node-app image, maps the container's port 3004 to the host's port 3004, and runs the application. You should be able to access your API at http://localhost:3005

# Test API with `curl`

```sh
  curl -X POST http://localhost:3005/api/customers/create -H "Content-Type: application/json" -d '{"first_name": "John", "last_name": "Doe"}'
```

# Test API with Postman

## Setup Postman

### Step 1: Create a New Collection

- Open postman
- Click on the Collections tab on the left sidebar.
- Click the New button and select Collection.
- Name your collection (e.g., "Customer API").

## Create Customer (POST)

- Click the Add Request button within your new collection.
- Name your request (e.g., "Create Customer").
- Set the `HTTP` method to `POST`.
- Enter the URL: http://localhost:3004/create-customer.
- Go to the Body tab, select raw and set the format to `JSON`
- Add the `JSON` payload for creating a new customer. Example
  ```json
  {
    "first_name": "Test Customer first_name 1",
    "last_name": "Test Customer last_name 1"
  }
  ```
- Click **Save** and then **Send** to test the request.
- Remarks:
  - To create multiple customers, specify the following in message body:
    ```json
    [
      {
        "first_name": "John",
        "last_name": "Doe"
      },
      {
        "first_name": "Jane",
        "last_name": "Smith"
      }
    ]
    ```

## Read Customers (GET)

- Add another request to the collection.
- Name your request (e.g., "**Read Customers**").
- Set the `HTTP` method to `GET`
- Enter the URL: http://localhost:3004/read-customer
- Click **Save** and then **Send** to test the request.

## Update Customer (PUT)

- Add another request to the collection.
- Name your request (e.g., "**Update Customer**").
- Set the `HTTP` method to `PUT`.
- Enter the URL: http://localhost:3004/update-customer/:id (replace :id with the actual customer ID).
- Go to the Body tab, select raw and set the format to JSON.
- Add the JSON payload for updating the customer. Example
  ```json
  {
    "first_name": "Updated First Name"
  }
  ```
- Click **Save** and then **Send** to test the request.

## Delete Customer (DELETE)

- Add another request to the collection.
- Name your request (e.g., "**Delete Customer**").
- Set the `HTTP` method to `DELETE`.
- Enter the URL: http://localhost:3004/delete-customer/:id (replace :id with the actual customer ID).
- Click **Save** and then **Send** to test the request.

# Resources and Further Reading
