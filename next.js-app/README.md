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

# Prisma

- There are many popular **ORM libraries** for **Node.js**: **Prisma**, **Sequelize**, **TypeORM**, and others.

## Why Use Prisma?

- In the simplest case, **Prisma** can access your database as an **ORM**. As part of its suite of products, **Prisma** offers a "**Client API**" that can make writing even the most complex database operations simple. But where **Prisma** shines is in its ability to handle complex querying operations.
- **Prisma**'s API lets you easily traverse relationships. Below is an example of an application accessing a database. First, the application accesses an author's profile by using the navigation properties from the blog post to the author and finally to the author's profile:
  ```prisma
    const authorProfile: Profile | null = await prisma.post
    .findUnique({ where: { id: 1 } })
    .author()
    .profile();
  ```
- It also makes pagination a breeze by exposing arguments for order, limits, and cursors. Below you can see an example where you can use the client to take five posts from the database by starting from the post with id=2:
  ```prisma
    // Find the next 5 posts after post id 2
    const paginatedPosts3: Post[] = await prisma.post.findMany({
      take: 5,
      cursor: {
        id: 2,
      },
    });
  ```
- It also allows for aggregate queries such as sum and count:
  ```prisma
    // Group users by country
    const groupUsers = await prisma.User.groupBy({
      by: ["country"],
      _count: {
        id: true,
      },
    });
  ```
- Along with these features, Prisma's client also facilitates transactions, includes middleware and the execution of raw questions, and helps make logging simple.
- But to limit **Prisma**'s capabilities to just reading or writing data would be a major disservice. Another great aspect of Prisma is how it handles migrations.

## The Prisma Schema

- The **Prisma schema** allows us to define application **models** in an intuitive data modeling language. It also contains the connection to a database and defines a generator:
- For **Relational Database**:

  ```prisma
    datasource db {
      provider = "postgresql"
      url      = env("DATABASE_URL")
    }

    generator client {
      provider = "prisma-client-js"
    }

    model Post {
      id        Int     @id @default(autoincrement())
      title     String
      content   String?
      published Boolean @default(false)
      author    User?   @relation(fields: [authorId], references: [id])
      authorId  Int?
    }

    model User {
      id    Int     @id @default(autoincrement())
      email String  @unique
      name  String?
      posts Post[]
    }
  ```

- For **MongoDB**:

  ```prisma
    datasource db {
      provider = "mongodb"
      url      = env("DATABASE_URL")
    }

    generator client {
      provider = "prisma-client-js"
    }

    model Post {
      id        String  @id @default(auto()) @map("_id") @db.ObjectId
      title     String
      content   String?
      published Boolean @default(false)
      author    User?   @relation(fields: [authorId], references: [id])
      authorId  String  @db.ObjectId
    }

    model User {
      id    String  @id @default(auto()) @map("_id") @db.ObjectId
      email String  @unique
      name  String?
      posts Post[]
    }
  ```

- Here, we have configured 3 things:
  - **Data source**: Specifies your database connection (via an environment variable)
  - **Generator**: Indicates that you want to generate Prisma Client
  - **Data model**: Defines your application models

## Configure Prisma

### Step 1: Installing the Prisma Client

- To start using **Prisma**, you will need the `prisma` and `@prisma/client` packages. `prisma` is the **Prisma CLI** tool while `@prisma/client` is an auto-generated query builder that will help you query your database.
- Install these two packages via `npm`
  ```sh
    npm i prisma @prisma/client
  ```
- or:
  ```sh
   npm install prisma --save-dev
   npm install @prisma/client
  ```
- Installing the `@prisma/client` package invokes the `prisma generate` command, which reads your **Prisma schema** and generates Prisma Client code. The code is generated into the `node_modules/.prisma/client` folder by default.

### Step 2: Initialize `prisma`

- Next, initialize `prisma` by running the below command on the terminal.
  ```sh
    npx prisma init
  ```
- This will generate a new file called `schema.prisma` which contains the database schema and a `.env` file to which you’ll add the database connection URL.
- After you change your **data model**, you'll need to manually re-generate **Prisma Client** to ensure the code inside `node_modules/.prisma/client` gets updated:
  ```sh
    prisma generate
  ```

### Step 3: Adding the Connection URL

- You need a **connection URL** to connect `prisma` to your **PostgreSQL database**. The general format for a connection URL is:
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

### Step 4: Defining the Database Schema

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

### Step 5: Using Prisma Client to send queries to your database

- Once **Prisma Client** has been generated, you can import it in your code and send queries to your database. This is what the setup code looks like
- Import and instantiate **Prisma Client**:
  ```javascript
  import { PrismaClient } from "@prisma/client";
  const prisma = new PrismaClient();
  ```
- Now you can start sending queries via the generated **Prisma Client API**, here are a few sample queries.
- Note that all Prisma Client queries return plain old JavaScript objects.
- Examples:
  - Retrieve all User records from the database
    ```js
    // Run inside `async` function
    const allUsers = await prisma.user.findMany();
    ```
  - Include the posts relation on each returned User object
    ```js
    // Run inside `async` function
    const allUsers = await prisma.user.findMany({
      include: { posts: true },
    });
    ```
  - Filter all Post records that contain "prisma"
    ```js
    // Run inside `async` function
    const filteredPosts = await prisma.post.findMany({
      where: {
        OR: [
          { title: { contains: "prisma" } },
          { content: { contains: "prisma" } },
        ],
      },
    });
    ```

### Step 6: Adjust Docker Configuration

- If you're running your application in **Docker**, ensure the `.env` file is copied into the Docker container. Your `Dockerfile` might look something like this:

  ```Dockerfile
    # Use the official Node.js image
    FROM node:14

    # Set the working directory
    WORKDIR /app

    # Copy the dependency files
    COPY package*.json ./

    # Install dependencies
    RUN npm install

    # Copy the rest of the application code
    COPY . .

    # Copy the .env file
    COPY .env .env

    # Ensure Prisma Client is generated
    RUN npx prisma generate

    # Expose the port the app runs on
    EXPOSE 3000

    # Run the app
    CMD ["npm", "run", "dev"]
  ```

# Resources and Further Reading

1. [github.com/nyangweso-rodgers - Setting up Next.js App](https://github.com/nyangweso-rodgers/Programming-with-JavaScript/blob/main/02-JavaScript-Libraries/01-React/03-React-Frameworks/01-Next.js/01-Setting-Next.js-App/Readme.md)
2. [github.com/iambstha - API request in nextjs app router](https://github.com/iambstha/blog-post-request-nextjs-app-router/tree/master)
3. [www.prisma.io/](https://www.prisma.io/)