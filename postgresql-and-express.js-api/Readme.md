# API with PostgreSQL, Prisma, Express.js, and Docker

# Description

- Develop an API with postgresql and express.

# Project Setup

## CREATE Customer

- For creating a single customer, we add the following to our `src/app/api/create-customer/route.js` file:

  ```javascript
  //create customer
  import { PrismaClient } from "@prisma/client";
  const prisma = new PrismaClient();

  async function createCustomer(req) {
    const customerData = req.body; // Assuming data is in request body
    console.log("Received customer data:", customerData);
    try {
      const newCustomer = await prisma.customer.create({ data: customerData }); // Pass data object
      return newCustomer; // Return the created customer data
    } catch (error) {
      console.error(error);
      throw error; // Re-throw for handling in app.js
    }
  }
  export default createCustomer;
  ```

- Remark:
  - **Prisma** does support batch creation of multiple records using the `createMany` method. This method allows you to efficiently insert multiple records into your database in a single operation, which can be more performant than creating each record individually.
- For creating multiple customers, we can use **Bulk Create with Prisma** (Prisma Version >= 2.20.0):

  - If you're using Prisma version 5.16.1 or above, you can leverage Prisma's createMany functionality.
  - This allows you to create multiple customers in a single request.

    ```js
    import { PrismaClient } from "@prisma/client";
    const prisma = new PrismaClient();

    async function createCustomer(req) {
      const customerData = req.body; // Assuming data is in request body
      console.log("Received customer data:", customerData);
      try {
        const newCustomer = await prisma.customer.createMany({
          data: customerData,
          skipDuplicates: true, // Optional: Avoid creating duplicates (unique constraints)
        }); // Pass data object
        return newCustomer; // Return the created customer data
      } catch (error) {
        console.error(error);
        throw error; // Re-throw for handling in app.js
      }
    }
    export default createCustomer;
    ```