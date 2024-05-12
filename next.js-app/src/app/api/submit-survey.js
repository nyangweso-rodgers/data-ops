import dbConnect from "../utils/db-connect";

import FormData from "../model/surveyDataSchema.js";

const Handler = async (req, res) => {
  try {
    // Ensure database connection before proceeding
    await dbConnect();

    if (req.method === "POST") {
      try {
        // Extract data from the request body
        const { firstName } = req.body; 

        // Create a new form data document
        const newFormData = await FormData.create({ firstName });

        res.status(201).json({ success: true, data: newFormData });
      } catch (error) {
        console.error("Error creating document:", error);
        res
          .status(500)
          .json({ success: false, error: "Internal Server Error" });
      }
    } else {
      res.status(405).json({ success: false, error: "Method Not Allowed" });
    }
  } catch (error) {
    // Handle connection error or other errors
    console.error("Error:", error);
    res.status(500).json({ success: false, error: "Internal Server Error" });
  }
};

export default Handler;