# Data Ops

# Project Description

- This prject is for:
  - **Data Pipeline** Service with **Apache Kafka**, **Postgres**, and **MongoDB**.
  - API service, and a
  - Next.js Application.

# Services

- The project has the following services running as Docker containers

  1. mongo
  2. postgres
  3. pgadmin
     - [dpage/pgadmin4](https://hub.docker.com/r/dpage/pgadmin4) is a web based administration tool for the PostgreSQL database.
  4. kafka
  5. kafka-ui
  6. zookeeper
  7. schema-registry
  8. sale-order-api
  9. customer-api
  10. nextjs.app

# Service 1: Running `mongo` Docker Container

- Check [github.com/nyangweso-rodgers - Run MongoDB Docker Container](https://github.com/nyangweso-rodgers/My-Databases/blob/main/03-Working-with-MongoDB/02-Setup-MongoDB/01-Run-MongoDB-Docker-Container/Readme.md) repo on how to run a mongo docker container using docker-compose.
- Check [github.com/nyangweso-rodgers - mongoDB replica set](https://github.com/nyangweso-rodgers/My-Databases/blob/main/03-Working-with-MongoDB/01-Fundamentals-of-MongoDB/mongoDB-replica-set/Readme.md) repo, to successfully set up a **MongoDB** **replica set** with **Docker Compose**. This ensures that you have a highly available and resilient MongoDB deployment.

# Service 2: Running `postgres` Docker Container

- Check my [github.com/nyangweso-rodgers - Running PostgreSQL Docker Container](https://github.com/nyangweso-rodgers/My-Databases/blob/my-dev-branch/02-Working-with-PostgreSQL/01-Setting-up-Postgres-on-Docker/01-With-Docker-Compose/Readme.md), GitHub repo on how to configure and run postgresql docker container using docker-compose.

# Connect to MongoDB

- Set up a **MongoDB** connection file to connect your app:

## Step 1: Install Dependencies

- Use `npm` or `yarn` to install the **MongoDB** driver and any other helper libraries:
  ```sh
    npm i mongodb
    npm i mongoose
  ```

## Step 2: Connect to MongoDB

- Set up a **MongoDB** connection file to connect your app

  ```js
  // .utils/mongodb-connect.js

  import mongoose from "mongoose";
  ```

# Fetching and Rendering Data with Next.js and MongoDB

# Resources and Further Reading

1. [github.com/nyangweso-rodgers - Docker-Commands](https://github.com/nyangweso-rodgers/My-Journey-Into-Computer-Science/blob/master/04-VMs-vs-Containers/02-Containers/01-Docker/01-Docker-Commands/Readme.md)

2. [github.com/nyangweso-rodgers - Setting Express.js Development Environment](https://github.com/nyangweso-rodgers/Programming-with-JavaScript/blob/main/03-JavaScript-Frameworks/02-Express.js/01-Setting-Express-Development-Environment/Readme.md)
3. [github.com/nyangweso-rodgers - Docker Compose File](https://github.com/nyangweso-rodgers/My-Journey-Into-Computer-Science/blob/master/04-VMs-vs-Containers/02-Containers/01-Docker/02-Docker-Compose-File/Readme.md)
