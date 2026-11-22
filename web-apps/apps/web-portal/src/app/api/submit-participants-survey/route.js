import connectToMongoDB from "../../utils/participants-survey-mongodb-connection.js";

import ParticipatsSurveyModel from "../../model/participants-survey-schema.js";

import { NextResponse } from "next/server";

export async function POST(req) {
  try {
    // Ensure database connection before proceeding (shared, cached connection:
    // don't close it per request, other requests may be using it).
    await connectToMongoDB();

    // Read and parse the request body
    const bodyObject = await req.json();

    console.log("Parsed bodyObject: ", bodyObject);

    // Access the firstName property directly from bodyObject
    const {
      firstName,
      lastName,
      gender,
      emailAddress,
      phoneNumber,
      nationality,
      currentResidence,
      message,
      agreedToTerms,
    } = bodyObject;

    await ParticipatsSurveyModel.create({
      firstName,
      lastName,
      gender,
      emailAddress,
      phoneNumber,
      nationality,
      currentResidence,
      message,
      agreedToTerms,
    });
    //console.log("Successfully Created Document ");

    return NextResponse.json(
      { message: "Participant's survey form submitted successfully" },
      { status: 201 }
    );
  } catch (error) {
    console.log(error);
    return NextResponse.json(
      { message: "Failed to submit Participant's survey form" },
      { status: 400 }
    );
  }
}
