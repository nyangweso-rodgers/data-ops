import bcrypt from "bcrypt";
import mongoose from "mongoose";

const { Schema, model } = mongoose;

const PERMISSION_LEVELS = {
  USER: 1,
  ADMIN: 2,
  SUPERADMIN: 3,
};

const userSchema = new Schema(
  {
    firstName: {
      type: String,
      required: "Your firstname is required",
      maxlength: 25,
    },
    lastName: {
      type: String,
      required: "Your lastname is required",
      maxlength: 25,
    },
    email: {
      type: String,
      required: "Your email is required",
      unique: true,
      lowercase: true,
      trim: true,
    },
    password: {
      type: String,
      required: "Your password is required",
      select: false,
      minlength: 8,
      maxlength: 128,
      // Add password strength validation using regular expression or library
    },
    permissionLevel: {
      type: Number,
      default: PERMISSION_LEVELS.USER,
      enum: Object.values(PERMISSION_LEVELS), // Example permission levels
    },
    createdBy: {
      type: String,
      required: true,
      default: "Rodgers Nyangweso",
    },
    updatedBy: {
      type: String,
      required: true,
      default: "Rodgers Nyangweso",
    },
  },
  { timestamps: true }
);
// Hash password before saving
userSchema.pre("save", async function (next) {
  // Check if the password field has been modified
  if (!this.isModified("password")) return next();

  try {
    // Hash the password with a salt factor of 10
    const saltRounds = 10; // Adjust as needed
    this.password = await bcrypt.hash(this.password, saltRounds);

    // Proceed to the next middleware or save operation
    next();
  } catch (error) {
    // Handle error, log it, and provide appropriate feedback to the user
    console.error("Error hashing password:", error);
    next(error);
  }
});

// Create and export the model
const usersModel = model("users", userSchema);
export default usersModel;
