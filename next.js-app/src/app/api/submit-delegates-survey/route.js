import DelegatesSurveySchema from "../../model/delegates-survey-schema.js";

import sequelizeInstance from "../../utils/delegates-survey-postgres-db-connect.js";

import { NextResponse } from "next/server";

export async function POST(req) {
  // Perform Sequelize sync before starting the server
  await sequelizeInstance.sync();

  try {
    // Read and parse the request body
    const bodyObject = await req.json();

    console.log("Parsed bodyObject: ", bodyObject);

    // Access the firstName property directly from bodyObject
    const { first_name, last_name, company_name } = bodyObject;

    await DelegatesSurveySchema.create({ first_name, last_name, company_name });
    console.log("Successfully Created Record");

    return NextResponse.json(
      { message: "Form submitted successfully" },
      { status: 201 }
    );
  } catch (error) {
    console.log(error);
    return NextResponse.json(
      { message: "Failed to submit form" },
      { status: 400 }
    );
  }
}
