# Sale Order REST API

## Table Of Contents

# Project Description

- Create a RESTful API with Node.js, Express.js and Docker. The application will connect to MongoDB, create a database and collection, insert a document, and expose an API endpoint to show the document with an HTTP request.

# Setup

- Check my [github.com/nyangweso-rodgers - Setting-Express-Development-Environment](https://github.com/nyangweso-rodgers/Programming-with-JavaScript/blob/main/03-JavaScript-Frameworks/02-Express.js/01-Setting-Express-Development-Environment/Readme.md) on how to setup an Express.js application with Docker and MongoDB.
- For the project we install the following dependencies:
  ```sh
    npm i express dotenv mongoose
  ```
  - `express` is for building the web server
  - `dotenv` is for loading environment variables from a `.env` file.
  - `mongoose`: An ODM (Object Data Modeling) library for MongoDB.
- Optional `dev-dependencies` (used for development purposes) include:
  ```sh
    #install dev-dependencies
    npm i nodemon morgan --save-dev
  ```
  - `nodemon`
  - `morgan`: provides requests details made. , it logs each request in the CLI. You will be able to see some information about the request.

# Connect to MongoDB Atlas or MongoDB Server Running on Docker

- We can either connecti to a **MongoDB Atlas** or **MongoDB server** running on **Docker**.
- For **MongoDB Atlas**, get connection string in this format:

  ```env
    MONGO_URI=mongodb+srv://<user_name>:<password>@test-cluster.uo4jsy5.mongodb.net/sale_orders_service?retryWrites=true&w=majority
  ```

- For **MongoDB server** running on **Docker**:
  ```env
    MONGO_URI=mongodb://root:root@0.0.0.0:27017/sale_order_service?authSource=admin
  ```

# Create a `Dockerfile`

```Dockerfile
    FROM node:alpine

    # Set the working directory inside the container
    WORKDIR /app

    # Copy package.json and package-lock.json to the working directory
    COPY package*.json ./

    # Install dependencies
    RUN npm install

    # Copy the rest of the application files
    COPY . .

    # Expose port
    EXPOSE 3200

    # Command to run the application
    CMD ["npm", "start"]
```

# Edit `docker-compose` File

# Further Reading
