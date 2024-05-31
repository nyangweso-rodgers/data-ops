import mongoDBConnect from "../../utils/participants-survey-mongo-db-connect.js";

import ParticipatsSurveyModel from "../../model/participants-survey-schema.js";

import mongoose from "mongoose";

import { NextResponse } from "next/server";

export async function POST(req) {
  // Ensure database connection before proceeding
  await mongoDBConnect();

  try {
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
    console.log("Successfully Created Document ");
    await mongoose.connection.close();

    return NextResponse.json(
      { message: "Form submitted successfully" },
      { status: 201 }
    );
  } catch (error) {
    console.log(error);
    await mongoose.connection.close();
    return NextResponse.json(
      { message: "Failed to submit form" },
      { status: 400 }
    );
  }
}
