# next.js Application

## Table Of Contents

# Setup

- Check my, [github.com/nyangweso-rodgers - Setting up Next.js App](https://github.com/nyangweso-rodgers/Programming-with-JavaScript/blob/main/02-JavaScript-Libraries/01-React/03-React-Frameworks/01-Next.js/01-Setting-Next.js-App/Readme.md) github repository on how to setup a Next.js Application with Docker.

# Next.js Back-End API

- In this API directory, we can create api endpoints that are executed exclusively on the backend.
- The Next.js App contains the following routes/endpoints:
  1. `/api/` - `POST` :
  2. `/api/` - `GET` :

#

- Each Next.js page component allows us to fetch data server-side thanks to a function called `getStaticProps`. When this function is called, the initial page load is rendered server-side, which is great for SEO. The page doesn't render until this function completes.

# Configure Prisma

## Step 1: Installing the Prisma Client

- To start using **Prisma**, you will need the `prisma` and `@prisma/client` packages. `prisma` is the **Prisma CLI** tool while `@prisma/client` is an auto-generated query builder that will help you query your database.
- Install these two packages via `npm`
  ```sh
    npm i prisma @prisma/client
  ```
- Next, initialize `prisma` by running the below command on the terminal.
  ```sh
    npx prisma init
  ```
- This will generate a new file called `schema.prisma` which contains the database schema and a `.env` file to which you’ll add the database connection URL.

## Step 2: Adding the Connection URL

- You need a connection URL to connect `prisma` to your **PostgreSQL database**. The general format for a connection URL is:
  ```sh
    postgres://{username}:{password}@{hostname}:{port}/{database-name}
  ```
- Replace the elements in curly brackets with your own database details then save it in the `.env` file:
- Then in `schema.prisma`, specify the database connection URL:

  ```prisma
    datasource db {
      provider = "PostgreSQL"
      url      = env("DATABASE_URL")
      }
  ```

## Step 3: Defining the Database Schema

- The **database schema** is a structure that defines the data model of your database. It specifies the tables, columns, and relationships between tables in the database, as well as any constraints and indexes the database should use.
- To create a **schema** for a database with a **users table**, open the `schema.prisma` file, and add a **User** model.
  ```prisma
    model User {
  id            String  @default(cuid()) @id
  name          String?
  email         String  @unique
  }
  ```
- The **User model** has an id column which is the primary key, a name column of type string, and an email column that should be unique.
- After defining the data model, you need to deploy your schema to the database using the npx prisma db push command.
  ```sh
    npx prisma db push
  ```
- This command creates the actual tables in the database.

# Using Prisma in Next.js

- To use **Prisma** in **Next.js**, you need to create a prisma client instance.
- First, generate the **Prisma client**.
  ```sh
    #generate prisma client
    npx prisma generate
  ```
- Then, create a new folder called `lib` and add a new file named `prisma.js` in it. In this file, add the following code to create a **prisma client** instance.

  ```js
  import { PrismaClient } from "@prisma/client";
  let prisma;

  if (typeof window === "undefined") {
    if (process.env.NODE_ENV === "production") {
      prisma = new PrismaClient();
    } else {
      if (!global.prisma) {
        global.prisma = new PrismaClient();
      }

      prisma = global.prisma;
    }
  }

  export default prisma;
  ```

- Now, you can import the prisma client as “prisma” in your files, and start querying the database.

# Querying the Database in a Next.js API Route

- **Prisma** is typically used on the server side, where it can safely interact with your database. In a **Next.js** application, you can set up an API route that uses **Prisma** to fetch data from the database and return it to the client. The pages or components can then fetch data from the API route using an HTTP library like `Axios` or `fetch`.
- Create the API route by opening the `pages/api` folder and creating a new subfolder named `db`. In this folder, create a file called `createuser.js` and add the following handler function.

  ```js
  import prisma from "@/lib/prisma";

  export default async function handler(req, res) {
    const { name, email } = req.query;

    try {
      const newUer = await prisma.User.create({
        data: {
          name,
          email,
        },
      });

      res.json({ user: newUer, error: null });
    } catch (error) {
      res.json({ error: error.message, user: null });
    }
  }
  ```

- This function gets the name and email from the request body. Then, in the `try/catch` block, it uses the create method provided by the **Prisma Client** to create a new user. The function returns a JSON object containing the user and the error message if any.
- In one of your components, you can now make a request to this API route.

# Resources and Further Reading

1. [github.com/nyangweso-rodgers - Setting up Next.js App](https://github.com/nyangweso-rodgers/Programming-with-JavaScript/blob/main/02-JavaScript-Libraries/01-React/03-React-Frameworks/01-Next.js/01-Setting-Next.js-App/Readme.md)
2. [github.com/iambstha - API request in nextjs app router](https://github.com/iambstha/blog-post-request-nextjs-app-router/tree/master)
