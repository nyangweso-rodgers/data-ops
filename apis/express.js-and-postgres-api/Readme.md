# API with Node.js, Express.js and PostgreSQL

## Table Of Contents

# Project Structure

1. `app.js`: The main entry point for the Express application, where the Express app is set up and middlewares, routes, etc., are applied.
2. `prisma/`: Contains the Prisma schema and migration files.
3. `src/`: The source code directory
   1. `controllers/`: Contains controller files, which handle **requests** and **responses**.
   2. `routes/`: Defines the application's routes, linking them to the corresponding **controllers**.
   3. `services/`: Contains business logic and service files that interact with the database through **Prisma**.

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
      url      = env("POSTGRES_TEST_DATABASE_URL")
      }

  ```

### Step 2.5: Prisma Migration

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
