# API with Node.js, Express.js and PostgreSQL

## Table Of Contents

# Description

- RESTful API built with Node.js and Express, designed to interact with a PostgreSQL database. The API provides endpoints for managing customer data and includes authentication features.
- **Features** include:
  1. **Get All Customers**: Retrieve a list of all customers
  2. **Get Customer by ID**: Retrieve a specific customer by their ID.
  3. **Create Customer**: Add a new Customer to the database.
  4. **Update Customer**: Update details of an existing Customer.
  5. **Delete Customer**: Remove a Customer from the database.
  6. **Customer Authentication**: Secure API access using JSON Web Tokens (JWT).

# Project Structure

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

## Step 2: Prisma Setup

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

## Step 3.1: `POST` customer

## Step 3.2: `GET` customer

## Step 3.1: `PUT` customer

## Step 3.1: `DELETE` customer

## Step 4: Dockerize the Application

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
