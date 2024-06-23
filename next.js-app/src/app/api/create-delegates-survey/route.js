//create a new delegates survey

import { PrismaClient } from "@prisma/client";
import { NextResponse } from "next/server";

console.log(
  "CREATE DELEGATES SURVEY DATABASE URL:",
  process.env.POSTGRES_TEST_DATABASE_URL
); // TODO: Add this line for debugging

const prisma = new PrismaClient();

export async function POST(req) {
  try {
    // Read and parse the request body
    const newDelegatesSurveyBodyObject = await req.json();

    console.log(
      "Parsed Delagets Survey Body Object: ",
      newDelegatesSurveyBodyObject
    );

    // Access the firstName property directly from customerBodyObject
    const { first_name, last_name, company_name } =
      newDelegatesSurveyBodyObject;

    // Create a new customer
    await prisma.delegatesSurvey.create({
      data: {
        first_name,
        last_name,
        company_name,
      },
    });

    return NextResponse.json(
      { message: "Delegates Survey Form submitted successfully" },
      { status: 201 }
    );
  } catch (error) {
    console.log("Error submitting delegates survey form:", error);
    return NextResponse.json(
      { message: "Failed to submit Delegates Survey Form" },
      { status: 400 }
    );
  }
}
