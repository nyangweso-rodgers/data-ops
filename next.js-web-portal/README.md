# Next.js Web Portal

## Table Of Contents

# Description

Create a Web Portal with Next.js.

# Setup

## Step 1: Setup Next.js Application with Docker

- Check my, [github.com/nyangweso-rodgers - Setting up Next.js App](https://github.com/nyangweso-rodgers/Programming-with-JavaScript/blob/main/02-JavaScript-Libraries/01-React/03-React-Frameworks/01-Next.js/01-Setting-Next.js-App/Readme.md) github repository on how to setup a **Next.js Application with Docker**.

## Step : Dockerize the application

```yml
verison: "1"
services:
  next.js-app:
    build:
      context: ./next.js-app
      dockerfile: Dockerfile
    image: next.js-app
    container_name: next.js-app
    ports:
      - "3003:3003"
    depends_on:
      - mongodb-community-server
      - postgres
    restart: always
```

## Step : Start the Next.js Docker Application

- Run the following command:
  ```bash
    docker-compose up -d --build next.js-app
  ```

## Step : Access Next.js Docker Application

- Access the application by:
  ```bash
    docker exec -it next.js-app bash
  ```

# Next.js Back-End API

- In this API directory, we can create api endpoints that are executed exclusively on the backend.
- The Next.js App contains the following routes/endpoints:
  1. `/api/` - `POST` :
  2. `/api/` - `GET` :

#

- Each Next.js page component allows us to fetch data server-side thanks to a function called `getStaticProps`. When this function is called, the initial page load is rendered server-side, which is great for SEO. The page doesn't render until this function completes.

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

    model User {
      id    String  @id @default(auto()) @map("_id") @db.ObjectId
      email String  @unique
      name  String?
    }
  ```

- Here, we have configured 3 things:
  - **Data source**: Specifies your database connection (via an environment variable)
  - **Generator**: Indicates that you want to generate Prisma Client
  - **Data model**: Defines your application models

## Prisma Migrate

- **Prisma Migrate** helps automate the process of managing changes in your codebase’s database schema. It generates a history of the migration file and allows you to keep your database schema in sync with your **Prisma schema** as it changes during development and production.
- Without **Prisma**, developers would have to manually write their SQL scripts to perform **migrations**. **Prisma Migrate** makes the process of managing database schema changes more streamlined and developer-friendly.
- To get started with **Prisma Migrate**, you once again need to create your **Prisma schema** first:

  ```prisma
    schema.prisma
    datasource db {
    url      = env("DATABASE_URL")
    provider = "sqlite"
    }

    generator client {
    provider = "prisma-client-js"
    }

    model User {
    id        Int      @id @default(autoincrement())
    name      String?
    }
  ```

- Next, we will, run the **migration command** to create our first migration:
  ```sh
    npx prisma migrate dev -name init
  ```
- Once done, we should see a success message. Now, your **Prisma schema** is in sync with your database schema. You should also now see a migration history
- Let’s say we have this schema defined for our application and we decide to make a change to the predefined model to add a new field called `address`. Remember that the model currently creates a table called `User` in our SQLite database. Now, let’s add the `address` field to the schema:

  ```prisma
    datasource db {
    url      = env("DATABASE_URL")
    provider = "sqlite"
    }

    generator client {
    provider = "prisma-client-js"
    }

    model User {
    id        Int      @id @default(autoincrement())
    name      String?
    address   String?
    }
  ```

- Next, since we added a new `address` field, let’s create our second migration:
  ```sh
    npx prisma migrate dev --name add_address_field
  ```
- You will be prompted to add a name for your migration:
- Enter the **migration name** and press Enter. You should see a success message once the migration is successful:
- Now, you should have a new migration history. You can have control over and deploy the changes. This is how **Prisma** streamlines database migrations and makes the process less complex.





## Step 5: Run Prisma Migrate Command from the Host

- Run the **Prisma migrate** command from within the your application docker container:
  ```bash
    docker exec -it next.js-app npx prisma migrate dev --name init
  ```
- This ensures the command uses the environment variables and network configuration within the container.

## Step 6: Update and Sync Prisma Schema Changes

- Suppose we make changes to the `schema.prisma` File by adding some fields. e.g.,

  - From:

    ```prisma
      datasource db {
      url      = env("DATABASE_URL")
      provider = "sqlite"
      }

      generator client {
      provider = "prisma-client-js"
      }

      model User {
      id        Int      @id @default(autoincrement())
      name      String?
      }
    ```

  - To:

    ```prisma
      datasource db {
      url      = env("DATABASE_URL")
      provider = "postgresql"
      }

      generator client {
      provider = "prisma-client-js"
      }

      model User {
      id        Int      @id @default(autoincrement())
      name      String?
      address   String?
      }
    ```

- To ensure your **PostgreSQL database schema** is up-to-date with your **Prisma schema** changes, you need to run the **Prisma migration** command inside the **Docker container** where your **Next.js app** is running. Here’s how you can do it:
- First, **Start your Docker containers**:
  ```sh
    docker-compose up -d -build next.js-app postgres
  ```
- **Run Prisma migration**: You need to execute the **Prisma migration command** inside the container where your Next.js app is running. You can do this by using the `docker-compose exec` command.
  ```sh
    docker-compose exec next.js-app npx prisma migrate dev --name add_created_by_field
  ```
  - This command will apply your migrations to the PostgreSQL database running in the Docker container.

# Resources and Further Reading

1. [github.com/nyangweso-rodgers - Setting up Next.js App](https://github.com/nyangweso-rodgers/Programming-with-JavaScript/blob/main/02-JavaScript-Libraries/01-React/03-React-Frameworks/01-Next.js/01-Setting-Next.js-App/Readme.md)
2. [github.com/iambstha - API request in nextjs app router](https://github.com/iambstha/blog-post-request-nextjs-app-router/tree/master)
