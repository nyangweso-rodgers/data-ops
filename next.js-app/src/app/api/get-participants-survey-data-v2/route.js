import connectToMongoDB from "../../utils/participants-survey-mongodb-connection.js";
import ParticipatsSurveyModel from "../../model/participants-survey-schema.js";
import { NextResponse } from "next/server.js";

export async function GET() {
  try {
    await connectToMongoDB();

    const participantsSurveyData = await ParticipatsSurveyModel.find();
    return NextResponse.json({ data: participantsSurveyData });
  } catch (error) {
    return NextResponse.json({ error });
  }
}
