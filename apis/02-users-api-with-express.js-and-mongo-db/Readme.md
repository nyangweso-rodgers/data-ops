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
    npm i express mongoose dotenv
  ```
- We will be using the following dependencies:
  1. [Mongoose](https://mongoosejs.com/), an object data modeling (**ODM**) library for MongoDB, to create the user model within the user schema.
  2. [Express.js]()

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

# Resources and Further Reading
