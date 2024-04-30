# Sale Order REST API Project using Express, Docker, and MongoDB

## Table Of Contents

# Project Description

- Create a RESTful API with Node.js, Express.js and Docker. The application will connect to MongoDB, create a database and collection, insert a document, and expose an API endpoint to show the document with an HTTP request.

# Project Setup

- For project setup, check my [github.com/nyangweso-rodgers - Setting Express Development Environment With MongoDB Docker Container](https://github.com/nyangweso-rodgers/Programming-with-JavaScript/blob/main/03-JavaScript-Frameworks/02-Express.js/01-Setting-Express-Development-Environment/02-With-MongoDB-Docker-Container/Readme.md) or [github.com/nyangweso-rodgers - Setting Express Development Environment With MongoDB Atlas](https://github.com/nyangweso-rodgers/Programming-with-JavaScript/blob/main/03-JavaScript-Frameworks/02-Express.js/01-Setting-Express-Development-Environment/01-With-MongoDB-Atlas/Readme.md) on how to setup an Express.js application with Docker and MongoDB.

# Connect to MongoDB Atlas or MongoDB Server Running on Docker

- We can either connecti to a **MongoDB Atlas** or **MongoDB server** running on **Docker**.
- For **MongoDB Atlas**, get connection string in this format:

  ```env
    MONGO_URI=mongodb+srv://<user_name>:<password>@test-cluster.uo4jsy5.mongodb.net/sale_orders_service?retryWrites=true&w=majority
  ```

- For **MongoDB server** running on **Docker**:
  - Ensure the connection string for MongoDB in your Node.js app or the associated environment variables is updated to:
- Syntax:
  ```env
    const MONGODB_URI = 'mongodb://mongo:27017/mydatabase';
  ```
- Example:
  ```env
    MONGO_URI=mongodb://mongo:27017/sale_order_service
  ```

# Dockerize the API

## Step #1: Create a `Dockerfile`

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

## Step #: Edit `docker-compose` File

# Test the API

## Step #: Test API with Postman

-

# Further Reading

1.
