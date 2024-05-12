import mongoose from "mongoose";

const surveyDataSchema = new mongoose.Schema({
  firstName: {
    type: String,
    required: true,
  },
  // Add other fields as needed
});

const FormData = mongoose.model("FormData", surveyDataSchema);

export default FormData;