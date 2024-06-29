# API with PostgreSQL, Prisma, Express.js, and Docker

# Description

- Develop an API with postgresql and express.

# Project Setup

## Step 1: Initialize Node.js App

- Initialize our Node.js app with:
  ```sh
      mkdir api-with-postgresql-and-express.js
      cd api-with-postgresql-and-express.js
      npm init -y
  ```
- Next, install necessary dependencies:
  ```sh
    npm i express dotenv
  ```

## Step 2: Setup Prisma ORM

### Step 2.1: Installing the Prisma Client

- To start using **Prisma**, you will need the `prisma` and `@prisma/client` packages. `prisma` is the **Prisma CLI** tool while `@prisma/client` is an auto-generated query builder that will help you query your database.
- Install these two packages via `npm`

  ```sh
    npm i prisma @prisma/client # instal these at the root of your project application
  ```

- Installing the `@prisma/client` package invokes the `prisma generate` command, which reads your **Prisma schema** and generates **Prisma Client** code. The code is generated into the `node_modules/.prisma/client` folder by default.

### Step 2.2: Initialize `prisma`

- Next, **initialize** `prisma` by running the below command on the terminal.
  ```sh
    npx prisma init
  ```
- This will generate a new file called `schema.prisma` which contains the database schema and a `.env` file to which you’ll add the **database connection URL**.

- **Remarks**:
  - After you change your **data model**, you'll need to manually re-generate **Prisma Client** to ensure the code inside `node_modules/.prisma/client` gets updated:
    ```sh
      npx prisma generate
    ```

### Step 2.3: Defining the Database Schema

- The **database schema** is a structure that defines the **data model** of your database. It specifies the tables, columns, and relationships between tables in the database, as well as any constraints and indexes the database should use.
- To create a **schema** for a database with a **customer table**, open the `schema.prisma` file, and add a **Customer** model.

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

- The **Customer model** has an `id` column which is the **primary key**.

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

- Till now **Prisma** and our **database** is completely separate! They are able to interact with each other but defining something in **prisma** won't do anything in the database!
- Suppose We made changes to our **schema**, To reflect those changes in our **DB**, we have to **migrate** our new schema! For that we have to use a command:
  ```bash
    npx prisma migrate dev --name init
  ```
  - Note: Here the `--name` is **optional**
- After that, It will create a **migration file** that will communicate with our **postgres database**.
- This file contains nothing but the SQL commands of our **schema**. It looks something like this:
  ```sql
    --migration.sql
    -- CreateTable
    CREATE TABLE "customer" ()
  ```

### Step 2.6: Use Prisma Client

```js
import { PrismaClient } from "@prisma/client";
const prisma = new PrismaClient();
```

- And with this we can perform our desired operations (like Create,Read,Update & Delete).

# CRUD Operations with Prisma Client

- Create an `app.js` file and start implementing CRUD!
  ```javascript
  import { PrismaClient } from "@prisma/client";
  const prisma = new PrismaClient();
  ```

# Define API Endpoints:

1. Use `app.post` for creating new customers (`/create-customer`).
2. Use `app.get` for fetching all customers (`/read-customers`).
3. Use `app.put` for updating existing customers (`/update-customer/:id`).
4. Use `app.delete` for deleting customers (`/delete-customer/:id`).

## CREATE customer

## READ Customers

- To, View all records add the following code to the main function:
- Remarkss:
  - We can also retrieve a single data with unique identifier!
    ```javascript
    const customerById = await prisma.customer.findUnique({
      where: { id: "" },
    });
    console.log(customerById);
    ```

## UPDATE

- Suppose We want to change the `first_name`, the code will be:

## DEELETE

# Create a `app.js` File

## Middleware

- `app.use(express.json())`: This **middleware** parses incoming request bodies in `JSON` format, allowing you to access data sent from the client in the `req.body` object.

# Dockerize the Application

## Running the Container

- Run the application by:

  ```bash
      docker-compose up -d --build api-with-postgresql-and-express.js
  ```

- This starts a container from the my-node-app image, maps the container's port 3004 to the host's port 3004, and runs the application. You should be able to access your API at http://localhost:3004.

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

1. []()
