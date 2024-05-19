import mongoose from "mongoose";
const { Schema, model } = mongoose;

const surveySchema = new Schema(
  {
    firstName: {
      type: String,
      //required: true,
    },
    // Add other fields as needed
  },
  { timestamps: true }
);

const SurveyModel = model("survey_data", surveySchema);

export default SurveyModel;