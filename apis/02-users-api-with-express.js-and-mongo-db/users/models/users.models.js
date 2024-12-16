import mongoose from "mongoose";
const { Schema, model } = mongoose;

const userSchema = new Schema({
  first_name: { type: String, required: true },
  last_name: { type: String, required: true },
  email: { type: String, required: true, unique: true },
  password: { type: String, required: true }, // Use a pre-save hook for hashing
  permission_level: { type: Number, default: 1 },
  created_by: { type: String, required: true, default: "Rodgers Nyangweso" },
  updated_by: { type: String, required: true, default: "Rodgers Nyangweso" },
});

// use the schema to create a model
const users = model("users", userSchema);
export default users;
