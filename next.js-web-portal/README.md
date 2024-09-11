# Next.js Web Portal

## Table Of Contents

## The Prisma Schema

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
