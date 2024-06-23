import { PrismaClient } from "@prisma/client";
//import { PrismaClient } from './node_modules/.prisma/client'
import { NextResponse } from "next/server";

console.log("REGISTER CUSTOMER DATABASE URL:", process.env.POSTGRES_TEST_DATABASE_URL); // TODO: Add this line for debugging


const prisma = new PrismaClient();

export async function POST(req) {
  try {
    // Read and parse the request body
    const newCustomerBodyObject = await req.json();

    console.log("Parsed Customer Body Object: ", newCustomerBodyObject);

    // Access the firstName property directly from customerBodyObject
    const { first_name, last_name } = newCustomerBodyObject;

    // Create a new customer
    await prisma.customer.create({
      data: {
        first_name,
        last_name,
        status, // This will default to TRUE if not provided
      },
    });

    return NextResponse.json(
      { message: "Customer Registration form submitted successfully" },
      { status: 201 }
    );
  } catch (error) {
    console.log("Error registering customer:", error);
    return NextResponse.json(
      { message: "Failed to submit Customer Registration Form" },
      { status: 400 }
    );
  }
}
