import mongoose from "mongoose";
const { Schema, model } = mongoose;

const surveySchema = new Schema(
  {
    createdBy: {
      type: "string",
      default: "Rodgers",
      required: true,
      immutable: true,
    },
    updatedBy: {
      type: "string",
      required: true,
      default: "Rodgers",
      immutable: false,
    },
    firstName: {
      type: String,
      required: true,
    },
    lastName: {
      type: String,
      required: true,
    },
    gender: {
      type: String,
      enum: ["Male", "Female"],
    },
    emailAddress: {
      type: String,
      required: true,
      immutable: true,
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
