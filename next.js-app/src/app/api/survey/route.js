import { NextResponse } from "next/server";

import mongoDBConnect from "../../utils/participants-survey-mongo-db-connect.js";

import ParticipatsSurveyModel from "../../model/participants-survey-schema.js";

export async function GET(res) {
  // Ensure database connection before proceeding
  await mongoDBConnect();

  try {
    const participantsSurveyData = await ParticipatsSurveyModel.find();
    console.log("MongoDB Participants Survey Data: ", participantsSurveyData);
    //res.status(200).json(participantsSurveyData);
    //res.json(participantsSurveyData); // Send data as JSON
    return NextResponse.json(participantsSurveyData);
  } catch (error) {
    //res.status(500).json({ error: "Failed to find participants survey data" });
    console.error("Error fetching participants survey data: ", error);
    return NextResponse.json(
      { error: "Failed to find participants survey data" },
      { status: 500 }
    );
  }
}
