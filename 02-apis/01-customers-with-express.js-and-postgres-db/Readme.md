# API with Node.js, Express.js and PostgreSQL

## Table Of Contents

## Creating a Secure REST API in Node.js, Express.js and PostgreSQL

## Table Of Contents

# Description

- **RESTful API** built with **Node.js** and **Express**, designed to interact with a **PostgreSQL database**. The API provides endpoints for managing `customer` data and includes authentication features.
- API **Features** include:
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

## 4. `src/routes/`

- **Routes** define the paths to different parts of your application and map them to the appropriate **controllers**.

## `src/middleware/`

- **Middleware** functions are used to process requests before they reach the **controllers**. They can handle tasks like **authentication**, **logging**, and request validation.
- Example:

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

# Testing API Endpoints Using curl

1. Create a new customer

   - Command:
   - Example: `curl -X POST http://localhost:3001/api/v1/customers/ -H "Content-Type: application/json" -d '{"first_name": "John", "last_name": "Doe"}'`

2. Get Customer By Id:

   - Command:
   - Example: `curl -X GET http://localhost:3001/api/v1/customers/205decf1-9e22-40bf-9713-5d28f29b6e1b`
   - Output:

3. Get Customers:

   - Command:
   - Example: `curl -X GET http://localhost:3001/api/v1/customers`

4. Delete Customer:
   - Command: `curl -X DELETE http://localhost:3001/api/v1/customers/{id}`
   - Example: `curl -X DELETE http://localhost:3001/api/v1/customers/40aebc7e-3f7e-49f5-bb4d-913f101737b4`

# Testing API Endpoints Using Postman

1. Create a new Customer

   - Request: `POST http://localhost:3001/api/v1/customers/`
   - Add the `JSON` payload for creating a new customer. Example

     ```json
     {
       "first_name": "Test Customer first_name 1",
       "last_name": "Test Customer last_name 1"
     }
     ```

   - Response
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

2. Get Customer By Id

   - Request: `GET http://<server_address>:<port>/api/v1/customers/:id`
   - Example: `GET http://localhost:3001/api/v1/customers/205decf1-9e22-40bf-9713-5d28f29b6e1b`
   - Response

3. Get Customers

   - Request: `GET http://<server_address>:<port>/api/v1/customers/`
   - Example: `GET http://localhost:3001/api/v1/customers/`
   - Response

4. Update Customer By Id:

   - Request: `PUT http://<server_address>:<port>/api/v1/customers/:id`
   - Example: `PUT http://localhost:3001/api/v1/customers/1a8e6a0d-a12f-41ae-8363-39ba6cfd1a16`
   - Message Body:
     ```json
     {
       "status": false
     }
     ```
   - Response

5. Delete Customer By Id:
   - Request: `DELETE http://localhost:3001/api/v1/customers/{id}`
   - Example: `DELETE http://localhost:3001/api/v1/customers/40aebc7e-3f7e-49f5-bb4d-913f101737b4`

# Resources and Further Reading
