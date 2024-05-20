import mongoose from "mongoose";
const { Schema, model } = mongoose;

const surveySchema = new Schema(
  {
    firstName: {
      type: String,
      required: true,
    },
    lastName: {
      type: String,
      required: true,
    },
    emailAddress: {
      type: String,
      required: true,
    },
    phoneNumber: {
      type: String,
      required: false,
    },
    message: {
      type: String,
      required: false,
    },
    // Add other fields as needed
  },
  { timestamps: true }
);

const SurveyModel = model("survey_data", surveySchema);

export default SurveyModel;
