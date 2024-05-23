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
    country: {
      type: String,
      default: "Kenya",
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
    agreedToTerms: {
      type: Boolean,
      required: true,
      default: false,
    },
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
  },
  { timestamps: true }
);

const SurveyModel = model("survey_data", surveySchema);

export default SurveyModel;
