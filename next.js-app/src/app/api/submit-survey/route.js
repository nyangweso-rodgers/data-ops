import dbConnect from "../../utils/db-connect";

import SurveyModel from "../../model/surveyDataSchema.js";

import mongoose from "mongoose";

import { NextResponse } from "next/server";

export async function POST(req) {
  // Ensure database connection before proceeding
  await dbConnect();

  try {
    // Read and parse the request body
    const bodyObject = await req.json();

    console.log("Parsed bodyObject: ", bodyObject);

    // Access the firstName property directly from bodyObject
    const { firstName, lastName } = bodyObject;

    await SurveyModel.create({ firstName, lastName });
    await mongoose.connection.close();

    return NextResponse.json(
      { message: "Message sent successfully" },
      { status: 201 }
    );
  } catch (error) {
    console.log(error);
    await mongoose.connection.close();
    return NextResponse.json(
      { message: "Failed to send message " },
      { status: 400 }
    );
  }
}
