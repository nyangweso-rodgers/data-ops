# API with Node.js, Express.js and PostgreSQL

## Creating a Secure REST API in Node.js, Express.js and PostgreSQL

## Table Of Contents

# Features

1. **User Management**:

   - **Get All Users**: Retrieve a list of all users.
   - **Get User by ID**: Retrieve a specific user by their ID.
   - **Create User**: Add a new user to the database.
   - **Update User**: Update details of an existing user.
   - **Delete User**: Remove a user from the database (soft delete functionality).

2. **Authentication & Authorization**:

   - **User Authentication**: Secure API access using **JSON Web Tokens** (**JWT**).
   - **Role-based Access Control** (**RBAC**): Control access to resources based on user roles (e.g., admin, user).

3. **Swagger API Documentation**:

   - **Swagger** integrated for real-time API documentation and testing directly in the browser.

4. **Database**

   - Integration with **MongoDB** for storing user data.
   - Soft delete functionality: Mark users as deleted without removing their data.

5. **Unit Testing**:
   - Comprehensive unit tests using [Mocha]() and [Chai]() to ensure the reliability of the application.
   - **Test Cases**: Includes tests for user creation, update, deletion, and authentication.

# Description

- Create a secure **REST API** for a resource called `users`.
- The resource will have the following structure:

  1. `id` (an auto-generated UUID)
  2. `firstName`
  3. `lastName`
  4. `email`
  5. `password`
  6. `permissionLevel` (what is this user allowed to do?)

- The resource will have the following operations:

  1. `POST` on the endpoint `/users` (create a new user)
  2. `GET` on the endpoint `/users` (list all users)
  3. `GET` on the endpoint `/users/:userId` (get a specific user)
  4. `PATCH` on the endpoint `/users/:userId` (update the data for a specific user)
  5. `DELETE` on the endpoint `/users/:userId` (remove a specific user)

- We will also be using **JSON web tokens** (**JWTs**) for access tokens. To that end, we will create another resource called auth that will expect a user’s email and password and, in return, will generate the token used for authentication on certain operations.

# Requirements

1. Latest Node.js version
2. MongoDB Installed
   - Remarks:
     - With **MongoDB**, there’s no need to create a specific database like there might be in some **RDBMS** scenarios. The first insert call from our **Node.js** code will trigger its creation automatically.

# Project Structure

- Project contains the following module folders:

  1. `common` (handling all shared services, and information shared between user modules)
  2. `users` (everything regarding users)
  3. `auth` (handling JWT generation and the login flow)

- Run `npm init -y ` to initialize the project or run `npm install` to install the project.
- Install the following dependencies
  ```sh
    npm i express mongoose dotenv bcrypt cookie-parser cors express-validator jsonwebtoken
  ```
- Additonally, install **Nodemon** as dev dependency:
  ```sh
    npm install --save-dev nodemon
  ```
- We will be using the following dependencies:
  1. [Mongoose](https://mongoosejs.com/), an object data modeling (**ODM**) library for **MongoDB** and **Node.js**., to create the user model within the user schema. It manages relationships between data, provides schema validation, and is used to translate between objects in code and the representation of those objects in **MongoDB**
  2. [Express.js](https://expressjs.com) is a minimal and flexible **Node.js** web application framework that provides a robust set of features for web and mobile applications.
  3. [Bcrypt]() is a library to help you hash passwords. It uses a password-hashing function that is based on the Blowfish cipher. We will use this to hash sensitive things like passwords.
  4. [Cookie-parser]() is a **middleware** used to parse the Cookie header and populate `req.cookies` with an object keyed by the cookie names. Optionally you may enable signed cookie support by passing a secret string, which assigns req.secret so it may be used by other middleware.
  5. [Dotenv]() is a zero-dependency module that loads environment variables from a `.env` file into `process.env`.
  6. [CORS]() is a node.js package for providing a Connect/Express middleware that can be used to enable CORS with various options. We don’t necessarily need this as we are developing just the API, however, good that you know in case you want to implement one.
  7. [Express-Validator]() is a set of express.js middlewares that wraps validator.js validator and sanitiser functions. You may want to check for an empty request body or validate or even sanitize the request body. This package is very useful for that. You will add one or two of its functions in your code later.
  8. [Nodemon]() is a tool that helps develop **Node.js** based applications by automatically restarting the node application when file changes in the directory are detected. With this, you don’t have to manually restart your application each time you make changes. Another powerful tool used mostly in production is pm2.

# Steps

## Step 1. Create Mongoose Schema

- First, we need to create the **Mongoose schema** in `/users/models/users.model.js`:
  ```javascript
  const userSchema = new Schema({
    firstName: String,
    lastName: String,
    email: String,
    password: String,
    permissionLevel: Number,
  });
  ```
- Once we define the schema, we can easily attach the schema to the user model.
  ```javascript
  const userModel = mongoose.model("Users", userSchema);
  ```
- After that, we can use this model to implement all the CRUD operations that we want within our Express.js endpoints.
- Let’s start with the “create user” operation by defining the Express.js route in `users/routes.config.js`:

## Step 2. Connect to MongoDB

- Create a `.env` file in the root directory and add the following:
  ```env
      MONGODB_URL=<Your MongoDB Connection String>
  ```

## Step 3. Create `app.js` Entrypoint File

- Create an `app.js` file in the root directory and add the following:

# Testing API Endpoints

1. Create a new User

   - Request: `POST http://localhost:3002/api/v1/users/`
   - Response

2. Fetch All users

   - Request: `GET http://localhost:3002/api/v1/users/`
   - Response:

3. Fetch a User by ID
   - Request:  `GET http://localhost:3002/api/v1/users/675ff32f25012b973cce49d6`
   - Response:

# Resources and Further Reading

1. [Build a Login and Logout API using Express.js (Node.js)](https://hackernoon.com/build-a-login-and-logout-api-using-expressjs-nodejs?ref=dailydev)
