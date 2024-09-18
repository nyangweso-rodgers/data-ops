import prisma from "../../../lib/prisma.js";

import { NextResponse } from "next/server";

export async function POST(req) {
  try {
    // Read and parse the request body
    const participantSurveyFormBodyObject = await req.json();

    const {
      firstName,
      lastName,
      emailAddress,
      phoneNumber,
      nationality,
      city,
      keepDoing,
      startDoing,
      stopDoing,
    } = participantSurveyFormBodyObject;

    await prisma.ParticipantsSurvey.create({
      data: {
        first_name: firstName,
        last_name: lastName,
        email: emailAddress,
        phone_number: phoneNumber,
        nationality: nationality,
        city: city,
        what_should_we_keep_doing: keepDoing,
        what_should_we_start_doing: startDoing,
        what_should_we_stop_doing: stopDoing,
      },
    });

    return NextResponse.json(
      {
        message: "Participant Survey Form Submitted Successfully",
      },
      { status: 201 }
    );
  } catch (error) {
    console.log("Error Submitting Participant Survey Form: ", error);
    return NextResponse.json(
      {
        message: "Failed To Submit Participant Survey Form",
      },
      { status: 400 }
    );
  }
}
