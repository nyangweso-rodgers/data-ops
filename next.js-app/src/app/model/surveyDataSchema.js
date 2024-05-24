import mongoose from "mongoose";
const { Schema, model } = mongoose;

const generateCode = () => {
  const prefix = "CS-";
  const dateTime = new Date()
    .toISOString()
    .replace(/[-:.TZ]/g, "")
    .slice(0, 12);
  return `${prefix}${dateTime}`;
};

const surveySchema = new Schema(
  {
    code: {
      type: String,
      unique: true,
      //required: true,
    },
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
      //required: true,
    },
    county: {
      type: String,
      default: "Nairobi",
    },
    gender: {
      type: String,
      enum: ["Male", "Female"],
    },
    emailAddress: {
      type: String,
      lowercase: true,
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
      default: "Rodgers Nyangweso",
      required: true,
      immutable: true,
    },
    updatedBy: {
      type: "string",
      required: true,
      default: "Rodgers Nyangweso",
      immutable: false,
    },
  },
  { timestamps: true }
);

// Pre-save middleware to generate the code
surveySchema.pre("save", function (next) {
  if (!this.code) {
    // Only set the code if it doesn't already exist
    this.code = generateCode();
  }
  next();
});

const SurveyModel = model("survey_data", surveySchema);

export default SurveyModel;
